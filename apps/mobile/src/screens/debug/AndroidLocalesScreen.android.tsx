import { useEffect, useState } from 'react';
import { ScrollView } from 'react-native';
import { runLocaleVerification } from '@lody-ios/kit';
import { AppText } from '@/ui/AppText';
import { definePage } from '@/lib/presentation';
import { usePalette } from '@/lib/theme/palette';
import en from '../../../locales/en.json';
import zh from '../../../locales/zh-Hans.json';

type Entry = {
  locale: string;
  key: string;
  count: number | null;
  arguments: Record<string, string>;
  text: string;
};
function AndroidLocalesScreen() {
  const colors = usePalette();
  const [status, setStatus] = useState('Checking native resources');
  const [examples, setExamples] = useState<string[]>([]);
  useEffect(() => {
    let active = true;
    void runLocaleVerification()
      .then((raw) => {
        const report = JSON.parse(raw) as {
          entries: Entry[];
          rejectedInvalidInputs: number;
        };
        if (report.rejectedInvalidInputs !== 4)
          throw new Error('Missing invalid-input checks');
        const expectedEntries = new Set<string>();
        for (const locale of ['en', 'zh-Hans', 'es']) {
          for (const key of Object.keys(en).filter(
            (value) => value.startsWith('native.') && !value.endsWith('.other'),
          )) {
            if (key.endsWith('.one')) {
              for (const count of [0, 1, 2])
                expectedEntries.add(`${locale}:${key.slice(0, -4)}:${count}`);
            } else expectedEntries.add(`${locale}:${key}:null`);
          }
        }
        for (const entry of report.entries) {
          if (
            !expectedEntries.delete(
              `${entry.locale}:${entry.key}:${entry.count}`,
            )
          )
            throw new Error('Unexpected or duplicate native resource');
          const catalog: Record<string, string> =
            entry.locale === 'zh-Hans' ? zh : en;
          let key = entry.key;
          if (entry.count !== null) {
            const category = new Intl.PluralRules(entry.locale).select(
              entry.count,
            );
            key += `.${category}`;
          }
          const template = catalog[key];
          if (template === undefined) throw new Error(`Missing source ${key}`);
          const values = { ...entry.arguments, count: String(entry.count) };
          const expected = template.replace(
            /\{([A-Za-z][A-Za-z0-9_]*)\}/g,
            (_, name: string) => values[name as keyof typeof values],
          );
          if (entry.text !== expected)
            throw new Error(`Resource mismatch: ${entry.locale} ${key}`);
        }
        if (expectedEntries.size)
          throw new Error('Native resources were skipped');
        if (!active) return;
        setExamples(
          report.entries
            .filter(
              (entry) =>
                entry.key === 'native.close' ||
                entry.key === 'native.chat.transcript.fileCount',
            )
            .map((entry) => `${entry.locale}: ${entry.text}`),
        );
        setStatus(
          `Native locales passed: ${report.entries.length} resources; 4 rejected inputs`,
        );
      })
      .catch((error: unknown) => {
        if (active) setStatus(`Native locales failed: ${String(error)}`);
      });
    return () => {
      active = false;
    };
  }, []);
  return (
    <ScrollView
      style={{ backgroundColor: colors.background }}
      contentContainerStyle={{ padding: 24, gap: 12 }}
    >
      <AppText variant="title">Android compiled language resources</AppText>
      <AppText>{status}</AppText>
      {examples.map((text, index) => (
        <AppText key={index}>{text}</AppText>
      ))}
    </ScrollView>
  );
}
export const androidLocalesPage = definePage({
  id: 'android-locales',
  title: 'Native languages',
  Component: AndroidLocalesScreen,
});
