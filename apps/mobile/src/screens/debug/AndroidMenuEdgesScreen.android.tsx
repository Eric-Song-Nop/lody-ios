import { useState } from 'react';
import { ScrollView, StatusBar } from 'react-native';
import { NativeMenuButton } from '@lody-ios/kit';
import { AppText } from '@/ui/AppText';
import { Button } from '@/ui/Button';
import { definePage } from '@/lib/presentation';
import { usePalette } from '@/lib/theme/palette';

const availableItems = [
  { id: 'edge', title: 'Enabled action', selected: true },
];
const emptyItems: typeof availableItems = [];
const avatar = { text: 'L', color: '#1565C0' };

function AndroidMenuEdgesScreen() {
  const colors = usePalette();
  const [enabled, setEnabled] = useState(true);
  const [selections, setSelections] = useState(0);
  return (
    <ScrollView
      style={{ backgroundColor: colors.background }}
      contentContainerStyle={{ padding: 24, gap: 16 }}
    >
      <StatusBar
        barStyle={colors.theme === 'dark' ? 'light-content' : 'dark-content'}
      />
      <AppText variant="title">Native menu edge cases</AppText>
      <AppText>Appearance: {colors.theme}</AppText>
      <AppText>
        Selections: {selections}; menu: {enabled ? 'enabled' : 'disabled'}
      </AppText>
      <NativeMenuButton
        accessibilityName="Edge menu"
        avatar={avatar}
        label="我的超长工作区名称不能折行 Long workspace title"
        items={enabled ? availableItems : emptyItems}
        onSelect={(id) => {
          if (id !== 'edge') throw new Error('Unexpected native menu action');
          setSelections((count) => count + 1);
        }}
      />
      <Button label="Disable menu" onPress={() => setEnabled(false)} />
      <Button label="Enable menu" onPress={() => setEnabled(true)} />
    </ScrollView>
  );
}

export const androidMenuEdgesPage = definePage({
  id: 'android-menu-edges',
  title: 'Menu edge cases',
  Component: AndroidMenuEdgesScreen,
});
