import { useState } from 'react';
import { ScrollView, TextInput } from 'react-native';
import {
  initialInboxView,
  saveInboxView,
  readInboxExpansion,
  saveInboxExpansion,
  copyText,
  selectionFeedback,
} from '@lody-ios/kit';
import { AppText } from '@/ui/AppText';
import { Button } from '@/ui/Button';
import { usePalette } from '@/lib/theme/palette';
import { definePage } from '@/lib/presentation';

const clipboardFixture = 'Lody 剪贴板 100% {literal}';
function AndroidSystemScreen() {
  const colors = usePalette();
  const [expansion, setExpansion] = useState(readInboxExpansion);
  const [saved, setSaved] = useState(false);
  const [pasted, setPasted] = useState('');
  const [feedback, setFeedback] = useState('not requested');
  return (
    <ScrollView
      style={{ backgroundColor: colors.background }}
      contentContainerStyle={{ padding: 24, gap: 16 }}
    >
      <AppText variant="title">Native system APIs</AppText>
      <AppText>Initial inbox view: {initialInboxView}</AppText>
      <AppText>
        Alpha: {String(expansion['verify-alpha'] ?? 'unset')}; Beta:{' '}
        {String(expansion['verify-beta'] ?? 'unset')}
      </AppText>
      <AppText>Preferences written: {String(saved)}</AppText>
      <Button
        label="Save inbox preferences"
        onPress={() => {
          saveInboxView(1);
          saveInboxExpansion('verify-alpha', true);
          saveInboxExpansion('verify-beta', false);
          setExpansion(readInboxExpansion());
          setSaved(true);
        }}
      />
      <Button
        label="Update alpha preference"
        onPress={() => {
          saveInboxExpansion('verify-alpha', false);
          setExpansion(readInboxExpansion());
        }}
      />
      <Button
        label="Copy fixture text"
        onPress={() => copyText(clipboardFixture)}
      />
      <TextInput
        accessibilityLabel="Paste fixture here"
        placeholder="Paste fixture here"
        value={pasted}
        onChangeText={setPasted}
        style={{
          minHeight: 48,
          borderWidth: 1,
          borderColor: colors.accent,
          color: colors.label,
          padding: 12,
          fontSize: 16,
        }}
      />
      <AppText>
        Clipboard paste matches: {String(pasted === clipboardFixture)}
      </AppText>
      <Button
        label="Request selection feedback"
        onPress={() => {
          void selectionFeedback()
            .then(() => setFeedback('resolved'))
            .catch(() => setFeedback('failed'));
        }}
      />
      <AppText>Feedback request: {feedback}</AppText>
    </ScrollView>
  );
}
export const androidSystemPage = definePage({
  id: 'android-system',
  title: 'System APIs',
  Component: AndroidSystemScreen,
});
