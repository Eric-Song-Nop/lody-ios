import { memo, useState } from 'react';
import { ScrollView, TextInput } from 'react-native';
import { NativeCloseButton } from '@lody-ios/kit';
import { AppText } from '@/ui/AppText';
import { definePage } from '@/lib/presentation';
import { usePalette } from '@/lib/theme/palette';
import { useTranslations } from '@/lib/i18n/useTranslations';

// No props change when the locale changes: this must subscribe independently.
const TranslatedCopy = memo(function TranslatedCopy() {
  const { locale, t, tp } = useTranslations();
  return (
    <>
      <AppText>Language snapshot: {locale}</AppText>
      <AppText>{t('native.close')}</AppText>
      <AppText>{tp('settings.machineCount', 1, { count: 1 })}</AppText>
      <AppText>{tp('settings.machineCount', 2, { count: 2 })}</AppText>
    </>
  );
});

function AndroidLocaleSwitchScreen() {
  const colors = usePalette();
  const [draft, setDraft] = useState('');
  const [presses, setPresses] = useState(0);
  return (
    <ScrollView
      keyboardShouldPersistTaps="handled"
      style={{ backgroundColor: colors.background }}
      contentContainerStyle={{ padding: 24, gap: 16 }}
    >
      <AppText variant="title">Runtime language verification</AppText>
      <TranslatedCopy />
      <TextInput
        accessibilityLabel="Language draft"
        value={draft}
        onChangeText={setDraft}
        selectionColor={colors.accent}
        cursorColor={colors.accent}
        style={{
          color: colors.label,
          borderColor: colors.accent,
          borderWidth: 1,
          padding: 12,
          minHeight: 48,
          fontSize: 17,
        }}
      />
      <AppText>Native presses: {presses}</AppText>
      <NativeCloseButton
        style={{ width: 48, height: 48 }}
        onPress={() => setPresses((value) => value + 1)}
      />
    </ScrollView>
  );
}

export const androidLocaleSwitchPage = definePage({
  id: 'android-locale-switch',
  title: 'Language switching',
  Component: AndroidLocaleSwitchScreen,
});
