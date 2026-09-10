import { useState } from 'react';
import { ScrollView, StatusBar, View } from 'react-native';
import {
  NativeSymbol,
  NativeSymbolButton,
  NativeGlassSurface,
} from '@lody-ios/kit';
import { Button } from '@/ui/Button';
import { AppText } from '@/ui/AppText';
import { usePalette } from '@/lib/theme/palette';
import { definePage } from '@/lib/presentation';

function AndroidControlsScreen() {
  const colors = usePalette();
  const [presses, setPresses] = useState(0);
  const [longPresses, setLongPresses] = useState(0);
  const [textPresses, setTextPresses] = useState(0);
  const [disabledPresses, setDisabledPresses] = useState(0);
  return (
    <ScrollView
      style={{ backgroundColor: colors.background }}
      contentContainerStyle={{ padding: 24, gap: 16 }}
    >
      <StatusBar
        barStyle={colors.theme === 'dark' ? 'light-content' : 'dark-content'}
      />
      <AppText variant="title">Native Android controls</AppText>
      <AppText>Appearance: {colors.theme}</AppText>
      <AppText>
        Icon presses: {presses}; long presses: {longPresses}
      </AppText>
      <AppText>
        Text presses: {textPresses}; disabled presses: {disabledPresses}
      </AppText>
      <View style={{ flexDirection: 'row', alignItems: 'center', gap: 16 }}>
        <NativeSymbol
          symbol="folder"
          pointSize={28}
          style={{ width: 48, height: 48 }}
        />
        <NativeSymbolButton
          symbol="plus"
          accessibilityName="Increment native counter"
          prominent
          style={{ width: 44, height: 44 }}
          onPress={() => setPresses((value) => value + 1)}
          onLongPress={() => setLongPresses((value) => value + 1)}
        />
        <NativeSymbolButton
          symbol="plus"
          accessibilityName="Disabled native counter"
          disabled
          style={{ width: 44, height: 44 }}
          onPress={() => setDisabledPresses((value) => value + 1)}
        />
      </View>
      <Button
        label="Native text action"
        variant="glass"
        onPress={() => setTextPresses((value) => value + 1)}
      />
      <Button
        label="Disabled text action"
        disabled
        onPress={() => setDisabledPresses((value) => value + 1)}
      />
      <View style={{ minHeight: 72, padding: 16, justifyContent: 'center' }}>
        <NativeGlassSurface />
        <AppText>Neutral native surface</AppText>
      </View>
      <AppText variant="mono">System monospace · 中文 · Aa 0123</AppText>
    </ScrollView>
  );
}

export const androidControlsPage = definePage({
  id: 'android-controls',
  title: 'Native controls',
  Component: AndroidControlsScreen,
});
