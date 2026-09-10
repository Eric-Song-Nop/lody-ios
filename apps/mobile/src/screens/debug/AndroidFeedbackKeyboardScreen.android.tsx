import { useState } from 'react';
import { ScrollView, TextInput } from 'react-native';
import { showToast } from '@lody-ios/kit';
import { Button } from '@/ui/Button';
import { AppText } from '@/ui/AppText';
import { usePalette } from '@/lib/theme/palette';
import { definePage } from '@/lib/presentation';

function AndroidFeedbackKeyboardScreen() {
  const colors = usePalette();
  const [draft, setDraft] = useState('Draft survives feedback');
  return (
    <ScrollView
      keyboardShouldPersistTaps="always"
      style={{ backgroundColor: colors.background }}
      contentContainerStyle={{ padding: 24, gap: 16 }}
    >
      <AppText variant="title">Feedback with keyboard</AppText>
      <TextInput
        accessibilityLabel="Feedback draft"
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
      <Button
        label="Show keyboard toast"
        onPress={() => showToast('Your draft remains available', 'info')}
      />
    </ScrollView>
  );
}

export const androidFeedbackKeyboardPage = definePage({
  id: 'android-feedback-keyboard',
  title: 'Keyboard feedback',
  Component: AndroidFeedbackKeyboardScreen,
});
