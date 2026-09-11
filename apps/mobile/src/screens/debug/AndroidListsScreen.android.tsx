import { useEffect, useRef, useState } from 'react';
import { View } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { NativeGroupedList } from '@lody-ios/kit';
import { AppText } from '@/ui/AppText';
import { Button } from '@/ui/Button';
import { definePage } from '@/lib/presentation';
import { usePageRuntime } from '@/hooks/screens/usePageRuntime';
import { usePalette } from '@/lib/theme/palette';

type SourceRowState = 'present' | 'removed' | 'disabled';
type DetailParams = { changeSourceRow: (state: SourceRowState) => void };

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
  const [prepended, setPrepended] = useState(false);
  const [lastAction, setLastAction] = useState('none');
  const [sourceRow, setSourceRow] = useState<SourceRowState>('present');
  const timer = useRef<ReturnType<typeof setTimeout> | null>(null);
  useEffect(
    () => () => {
      if (timer.current) clearTimeout(timer.current);
    },
    [],
  );
  const navigationRow = {
    id: 'open',
    title: 'Open list detail',
    subtitle:
      sourceRow === 'present'
        ? '原生导航行 · Native navigation'
        : 'Navigation unavailable',
    image: 'folder',
    navigates: sourceRow === 'present',
    disclosure: sourceRow === 'present',
  };
  let sections = [
    {
      id: 'main',
      header: 'Native grouped rows',
      footer: 'Actions return their stable row ID.',
      rows: [
        ...(sourceRow === 'removed' ? [] : [navigationRow]),
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
      rows: [
        ...Array.from({ length: prepended ? 20 : 0 }, (_, index) => ({
          id: `prepended-${index}`,
          title: `Prepended row ${index}`,
          action: true,
        })),
        ...Array.from({ length: 60 }, (_, index) => ({
          id: `row-${index}`,
          title: `History row ${index}`,
          action: true,
        })),
      ],
    },
  ];
  if (empty) sections = [];
  return (
    <View style={{ flex: 1, backgroundColor: colors.background }}>
      <View style={{ padding: 16, gap: 8 }}>
        <AppText>
          Actions: {actions}; returns: {returns}; refreshes: {refreshes}
        </AppText>
        <AppText variant="meta">Last row: {lastAction}</AppText>
        <Button label="Update row" onPress={() => setUpdated(true)} />
        <Button
          label={empty ? 'Restore list' : 'Empty list'}
          onPress={() => setEmpty((value) => !value)}
        />
        <Button
          label={prepended ? 'Remove prepended rows' : 'Prepend history'}
          onPress={() => setPrepended((value) => !value)}
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
              .push(detailPage, { changeSourceRow: setSourceRow })
              .then(() => setReturns((count) => count + 1));
            return;
          }
          if (id === 'static' || id === 'long')
            throw new Error('Static row dispatched');
          setLastAction(id);
          setActions((count) => count + 1);
        }}
      />
    </View>
  );
}
function AndroidListDetailScreen() {
  const colors = usePalette();
  const runtime = usePageRuntime<DetailParams>();
  const [sourceRow, setSourceRow] = useState<SourceRowState>('present');
  const changeSourceRow = (state: SourceRowState) => {
    runtime.params.changeSourceRow(state);
    setSourceRow(state);
  };
  return (
    <View style={{ flex: 1, padding: 24, backgroundColor: colors.background }}>
      <AppText>Native list detail</AppText>
      <AppText>Source row: {sourceRow}</AppText>
      <Button
        label="Remove source row"
        onPress={() => changeSourceRow('removed')}
      />
      <Button
        label="Disable source navigation"
        onPress={() => changeSourceRow('disabled')}
      />
    </View>
  );
}
const detailPage = definePage<DetailParams>({
  id: 'android-list-detail',
  title: 'List detail',
  Component: AndroidListDetailScreen,
  parseRouteParams: () => {
    throw new Error('List detail requires an in-memory source row owner');
  },
});
export const androidListsPage = definePage({
  id: 'android-lists',
  title: 'Grouped lists',
  Component: AndroidListsScreen,
});
