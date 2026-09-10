import { useEffect, useRef, useState } from 'react';
import { ScrollView } from 'react-native';
import {
  dismissSessionBanner,
  showSessionBanner,
  showToast,
} from '@lody-ios/kit';
import { Button } from '@/ui/Button';
import { AppText } from '@/ui/AppText';
import { usePalette } from '@/lib/theme/palette';
import { definePage } from '@/lib/presentation';

function AndroidFeedbackScreen() {
  const colors = usePalette();
  const [presses, setPresses] = useState(0);
  const timer = useRef<ReturnType<typeof setTimeout> | undefined>(undefined);
  useEffect(() => () => clearTimeout(timer.current), []);
  return (
    <ScrollView
      style={{ backgroundColor: colors.background }}
      contentContainerStyle={{ padding: 24, gap: 12 }}
    >
      <AppText variant="title">Native Android feedback</AppText>
      <AppText>
        Appearance: {colors.theme}; presses: {presses}
      </AppText>
      <Button
        label="Page still interactive"
        onPress={() => setPresses((value) => value + 1)}
      />
      <Button
        label="Show info toast"
        onPress={() => showToast('Saved locally — 本机保存 100%', 'info')}
      />
      <Button
        label="Show warning toast"
        onPress={() => showToast('Connection needs attention', 'warning')}
      />
      <Button
        label="Show error toast"
        onPress={() =>
          showToast('Upload failed; your draft is preserved', 'error')
        }
      />
      <Button
        label="Show toast burst"
        onPress={() => {
          showToast('Burst one', 'info');
          showToast('Burst two', 'warning');
          showToast('Burst three', 'error');
          showToast('Burst four', 'info');
          showToast('Burst four', 'info');
        }}
      />
      <Button
        label="Show completed banner"
        onPress={() =>
          showSessionBanner('Offline reply completed', 'completed')
        }
      />
      <Button
        label="Show attention banner"
        onPress={() =>
          showSessionBanner('Offline approval required', 'attention')
        }
      />
      <Button label="Dismiss session banner" onPress={dismissSessionBanner} />
      <Button
        label="Show delayed toast"
        onPress={() => {
          clearTimeout(timer.current);
          timer.current = setTimeout(
            () => showToast('Delayed native feedback', 'info'),
            5000,
          );
        }}
      />
    </ScrollView>
  );
}

export const androidFeedbackPage = definePage({
  id: 'android-feedback',
  title: 'Native feedback',
  Component: AndroidFeedbackScreen,
});
