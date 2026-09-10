import { useState } from 'react';
import { ScrollView, View } from 'react-native';
import { NativeSymbol, NativeSymbolButton } from '@lody-ios/kit';
import androidSymbolFixture from '@/features/debug/androidSymbols.json';
import { usePalette } from '@/lib/theme/palette';
import { definePage } from '@/lib/presentation';
import { AppText } from '@/ui/AppText';
import { Button } from '@/ui/Button';

const batchSize = 6;
const batchCount = Math.ceil(androidSymbolFixture.length / batchSize);

function AndroidSymbolsScreen() {
  const colors = usePalette();
  const [batch, setBatch] = useState(0);
  const [pressed, setPressed] = useState('none');
  const names = androidSymbolFixture.slice(
    batch * batchSize,
    (batch + 1) * batchSize,
  );
  return (
    <ScrollView
      style={{ backgroundColor: colors.background }}
      contentContainerStyle={{ padding: 16, gap: 8 }}
    >
      <AppText variant="title">Native symbol catalog</AppText>
      <AppText>
        Batch {batch + 1}/{batchCount} · {colors.theme}
      </AppText>
      <AppText>Pressed: {pressed}</AppText>
      {names.map((symbol, index) => (
        <View
          key={index}
          style={{
            flexDirection: 'row',
            alignItems: 'center',
            gap: 8,
            minHeight: 56,
          }}
        >
          <NativeSymbol
            symbol={symbol}
            pointSize={24}
            style={{ width: 32, height: 32 }}
          />
          <AppText style={{ flex: 1 }}>{symbol}</AppText>
          <NativeSymbolButton
            symbol={symbol}
            accessibilityName={`Activate ${symbol}`}
            onPress={() => setPressed(symbol)}
          />
        </View>
      ))}
      <Button
        label="Next symbols"
        disabled={batch + 1 === batchCount}
        onPress={() => setBatch((value) => value + 1)}
      />
    </ScrollView>
  );
}

export const androidSymbolsPage = definePage({
  id: 'android-symbols',
  title: 'Symbols',
  Component: AndroidSymbolsScreen,
});
