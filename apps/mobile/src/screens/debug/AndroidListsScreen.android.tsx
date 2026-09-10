import { useEffect, useRef, useState } from 'react';
import { View } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { NativeGroupedList } from '@lody-ios/kit';
import { AppText } from '@/ui/AppText';
import { Button } from '@/ui/Button';
import { definePage } from '@/lib/presentation';
import { usePageRuntime } from '@/hooks/screens/usePageRuntime';
import { usePalette } from '@/lib/theme/palette';

function AndroidListsScreen() {
  const colors = usePalette();
  const runtime = usePageRuntime();
  const insets = useSafeAreaInsets();
  const [actions, setActions] = useState(0);
  const [returns, setReturns] = useState(0);
  const [updated, setUpdated] = useState(false);
  const [empty, setEmpty] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const [refreshes, setRefreshes] = useState(0);
  const timer = useRef<ReturnType<typeof setTimeout> | null>(null);
  useEffect(
    () => () => {
      if (timer.current) clearTimeout(timer.current);
    },
    [],
  );
  const sections = empty
    ? []
    : [
        {
          id: 'main',
          header: 'Native grouped rows',
          footer: 'Actions return their stable row ID.',
          rows: [
            {
              id: 'open',
              title: 'Open list detail',
              subtitle: '原生导航行 · Native navigation',
              image: 'folder',
              navigates: true,
              disclosure: true,
            },
            {
              id: 'action',
              title: updated ? 'Updated action' : 'Count action',
              value: String(actions),
              action: true,
            },
            {
              id: 'static',
              title: 'Read-only information',
              subtitle: 'This row must not dispatch',
              value: 'Local',
            },
            {
              id: 'long',
              title:
                '这是一段需要自然换行的中文长标题，保持系统文字行为 Long text should wrap without clipping',
              subtitle: '/workspace/source/README.md',
              subtitleMono: true,
            },
          ],
        },
        { id: 'empty-group', header: 'Empty group', rows: [] },
        {
          id: 'history',
          header: 'Scrollable rows',
          rows: Array.from({ length: 60 }, (_, index) => ({
            id: `row-${index}`,
            title: `History row ${index}`,
            action: true,
          })),
        },
      ];
  return (
    <View style={{ flex: 1, backgroundColor: colors.background }}>
      <View style={{ padding: 16, gap: 8 }}>
        <AppText>
          Actions: {actions}; returns: {returns}; refreshes: {refreshes}
        </AppText>
        <Button label="Update row" onPress={() => setUpdated(true)} />
        <Button
          label={empty ? 'Restore list' : 'Empty list'}
          onPress={() => setEmpty((value) => !value)}
        />
      </View>
      <NativeGroupedList
        style={{ flex: 1 }}
        sections={sections}
        placeholder="No local rows"
        bottomInset={insets.bottom}
        refreshing={refreshing}
        onRefresh={() => {
          if (timer.current) return;
          setRefreshing(true);
          setRefreshes((count) => count + 1);
          timer.current = setTimeout(() => {
            setRefreshing(false);
            timer.current = null;
          }, 800);
        }}
        onRowPress={({ nativeEvent: { id } }) => {
          if (id === 'open') {
            void runtime
              .push(detailPage)
              .then(() => setReturns((count) => count + 1));
            return;
          }
          if (id === 'static' || id === 'long')
            throw new Error('Static row dispatched');
          setActions((count) => count + 1);
        }}
      />
    </View>
  );
}
function AndroidListDetailScreen() {
  const colors = usePalette();
  return (
    <View style={{ flex: 1, padding: 24, backgroundColor: colors.background }}>
      <AppText>Native list detail</AppText>
    </View>
  );
}
const detailPage = definePage({
  id: 'android-list-detail',
  title: 'List detail',
  Component: AndroidListDetailScreen,
});
export const androidListsPage = definePage({
  id: 'android-lists',
  title: 'Grouped lists',
  Component: AndroidListsScreen,
});
