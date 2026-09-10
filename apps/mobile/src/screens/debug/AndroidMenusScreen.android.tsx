import { useEffect, useMemo, useRef, useState } from 'react';
import { ScrollView, StatusBar } from 'react-native';
import { NativeContextMenu, NativeMenuButton } from '@lody-ios/kit';
import { Button } from '@/ui/Button';
import { AppText } from '@/ui/AppText';
import { usePalette } from '@/lib/theme/palette';
import { definePage } from '@/lib/presentation';

const actions = [
  { id: 'inspect', title: 'Inspect item', symbol: 'info.circle' },
  { id: 'remove', title: 'Remove item', symbol: 'xmark', destructive: true },
];
const avatar = { text: 'L', color: '#1565C0' };

function AndroidMenusScreen() {
  const colors = usePalette();
  const [selected, setSelected] = useState('all');
  const [selections, setSelections] = useState(0);
  const [lastAction, setLastAction] = useState('none');
  const [actionCount, setActionCount] = useState(0);
  const [childPresses, setChildPresses] = useState(0);
  const [anchorsVisible, setAnchorsVisible] = useState(true);
  const timer = useRef<ReturnType<typeof setTimeout> | undefined>(undefined);
  useEffect(() => () => clearTimeout(timer.current), []);
  const items = useMemo(
    () => [
      {
        id: 'all',
        title: 'All items',
        symbol: 'folder',
        selected: selected === 'all',
      },
      {
        id: 'recent',
        title: 'Recent items',
        symbol: 'circle',
        selected: selected === 'recent',
      },
    ],
    [selected],
  );
  return (
    <ScrollView
      style={{ backgroundColor: colors.background }}
      contentContainerStyle={{ padding: 24, gap: 16 }}
    >
      <StatusBar
        barStyle={colors.theme === 'dark' ? 'light-content' : 'dark-content'}
      />
      <AppText variant="title">Native Android menus</AppText>
      <AppText>Appearance: {colors.theme}</AppText>
      <AppText>
        Selected: {selected}; selections: {selections}
      </AppText>
      <AppText>
        Action: {lastAction}; actions: {actionCount}; child presses:{' '}
        {childPresses}
      </AppText>
      <AppText>Anchors: {anchorsVisible ? 'visible' : 'removed'}</AppText>
      {anchorsVisible && (
        <>
          <NativeMenuButton
            accessibilityName="Choose item filter"
            label="Item filter"
            avatar={avatar}
            items={items}
            onSelect={(id) => {
              setSelected(id);
              setSelections((count) => count + 1);
            }}
          />
          <NativeContextMenu
            accessibilityLabel="Item context actions"
            actions={actions}
            onAction={({ nativeEvent }) => {
              setLastAction(nativeEvent.id);
              setActionCount((count) => count + 1);
            }}
          >
            <Button
              label="Context item"
              variant="glass"
              onPress={() => setChildPresses((count) => count + 1)}
            />
          </NativeContextMenu>
        </>
      )}
      <Button
        label="Remove anchors after delay"
        onPress={() => {
          clearTimeout(timer.current);
          timer.current = setTimeout(() => setAnchorsVisible(false), 5000);
        }}
      />
      <Button label="Restore anchors" onPress={() => setAnchorsVisible(true)} />
    </ScrollView>
  );
}

export const androidMenusPage = definePage({
  id: 'android-menus',
  title: 'Native menus',
  Component: AndroidMenusScreen,
});
