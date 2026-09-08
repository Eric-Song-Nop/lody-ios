import {
  NativeGroupedList,
  type NativeListRow,
  type NativeListSection,
} from '@lody-ios/kit';
import { definePage } from '@/lib/presentation';
import { usePageRuntime } from '@/hooks/screens/usePageRuntime';
import { usePalette } from '@/lib/theme/palette';
import { bundledLicenses } from '@/features/licenses';
import { LicenseDetailScreen } from './LicenseDetailScreen';
import { t } from '../lib/i18n/index.ts';

/** Groups by the first letter of the name, ignoring the npm scope. */
function groupLetter(name: string) {
  const bare = name.startsWith('@') ? (name.split('/')[1] ?? name) : name;
  const letter = bare.slice(0, 1).toUpperCase();
  return /[A-Z]/.test(letter) ? letter : '#';
}

function licenseSections(): NativeListSection[] {
  const { packages } = bundledLicenses();
  const grouped = new Map<string, NativeListRow[]>();
  for (const entry of packages) {
    const letter = groupLetter(entry.name);
    const rows = grouped.get(letter) ?? [];
    rows.push({
      id: entry.name,
      title: entry.name,
      subtitle: entry.license,
      value: entry.version ? `v${entry.version}` : undefined,
      action: true,
      disclosure: true,
      navigates: true,
    });
    grouped.set(letter, rows);
  }
  const sections: NativeListSection[] = [...grouped]
    .sort(([left], [right]) => {
      if (left === '#') return 1;
      if (right === '#') return -1;
      return left.localeCompare(right, 'en');
    })
    .map(([letter, rows]) => ({ id: letter, header: letter, rows }));
  const last = sections[sections.length - 1];
  if (last) last.footer = t('settings.licenses.footer');
  return sections;
}

function View() {
  const colors = usePalette();
  const { push } = usePageRuntime();
  const sections = licenseSections();
  return (
    <NativeGroupedList
      style={{ flex: 1 }}
      accent={colors.accent}
      placeholder=""
      sections={sections}
      onRowPress={({ nativeEvent }) => {
        if (!nativeEvent.id) return;
        void push(
          LicenseDetailScreen,
          { name: nativeEvent.id },
          { title: nativeEvent.id },
        );
      }}
    />
  );
}

export const LicensesScreen = definePage({
  id: 'licenses',
  title: t('settings.licenses.title'),
  Component: View,
  presentation: { style: 'push', headerVariant: 'transparent' },
});
