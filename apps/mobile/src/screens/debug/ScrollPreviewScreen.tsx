import { Stack } from 'expo-router';
import { useEffect, useState } from 'react';
import { NativeChat } from '@lody-ios/kit';
import { definePage, usePageRuntime } from '@/presentation';
import { useProcessSheet } from '@/hooks/screens/useProcessSheet';

const cached = Array.from({ length: 12 }, (_, index) => ({
  id: `scroll-cache-${index}`,
  role: index % 2 ? 'assistant' : 'user',
  status: 'completed',
  finished: true,
  items: [
    {
      itemId: 'text',
      type: 'text',
      text: `缓存消息 ${index}\n\n保留阅读位置，等待最新历史。\n\n这段内容已经显示在本地。`,
    },
  ],
}));
const latest = [
  ...cached.map((entry, index) =>
    index === 8
      ? {
          ...entry,
          items: [
            {
              itemId: 'text',
              type: 'text',
              text: `${entry.items[0].text}\n\n同步补全了上方的内容。\n\n可见消息的位置应保持不变。`,
            },
          ],
        }
      : entry,
  ),
  ...Array.from({ length: 6 }, (_, index) => ({
    id: `scroll-new-${index}`,
    role: index % 2 ? 'assistant' : 'user',
    status: 'completed',
    finished: true,
    items: [
      {
        itemId: 'text',
        type: 'text',
        text: `新消息 ${index}\n\n从旧缓存平滑滚动到这里。\n\n末尾标记 ${index}。`,
      },
    ],
  })),
];
const lines = Array.from(
  { length: 18 },
  (_, index) => `第 ${index + 1} 行：正文持续增长，后面的行应连续移动。`,
).join('\n\n');
const code = `\n\n\`\`\`swift\n${Array.from({ length: 12 }, (_, index) => `let value${index} = ${index}`).join('\n')}\n\`\`\`\n\n流式输出结束。`;
const text = lines + code;

function View() {
  const { cancel } = usePageRuntime();
  const [mode, setMode] = useState<'cache' | 'live' | 'stream'>('cache');
  const [length, setLength] = useState(0);
  const [run, setRun] = useState(0);
  useEffect(() => {
    if (mode !== 'stream') return;
    const timer = setInterval(
      () => setLength((old) => Math.min(text.length, old + 80)),
      450,
    );
    return () => clearInterval(timer);
  }, [mode, run]);
  let entries = cached;
  if (mode === 'live') entries = latest;
  if (mode === 'stream')
    entries = [
      ...cached,
      {
        id: 'scroll-stream',
        role: 'assistant',
        status: 'running',
        finished: false,
        items: [
          {
            itemId: 'body',
            type: 'text',
            text: text.slice(0, Math.max(1, length)),
          },
          {
            itemId: 'tail',
            type: 'text',
            text: '尾部标记：跟随上一行的高度变化。',
          },
        ],
      },
    ];
  const entriesJSON = JSON.stringify(entries);
  const openProcess = useProcessSheet(entriesJSON, () => {});
  return (
    <>
      <Stack.Toolbar placement="left">
        <Stack.Toolbar.Button
          accessibilityLabel="Cached History"
          icon="arrow.counterclockwise"
          onPress={() => {
            setMode('cache');
            setRun((old) => old + 1);
          }}
        />
        <Stack.Toolbar.Button
          accessibilityLabel="Sync History"
          icon="arrow.down.circle"
          onPress={() => setMode('live')}
        />
      </Stack.Toolbar>
      <Stack.Toolbar placement="right">
        <Stack.Toolbar.Button
          accessibilityLabel="Stream Lines"
          icon="play"
          onPress={() => {
            setLength(0);
            setMode('stream');
            setRun((old) => old + 1);
          }}
        />
        <Stack.Toolbar.Button
          accessibilityLabel="Stream Process"
          icon="list.bullet"
          onPress={() => {
            setLength(0);
            setMode('stream');
            void openProcess('scroll-stream');
          }}
        />
        <Stack.Toolbar.Button
          accessibilityLabel="Finish Trace"
          icon="checkmark"
          onPress={cancel}
        />
      </Stack.Toolbar>
      <NativeChat
        key={run}
        style={{ flex: 1 }}
        navigationTitle="滚动连续性验收"
        entriesJSON={entriesJSON}
        composerJSON='{"editable":true,"canSend":false}'
        clearDraftToken={0}
        emptyText=""
        onSend={() => {}}
        onActivityPress={() => {}}
        onReconnect={() => {}}
      />
    </>
  );
}

export const ScrollPreviewScreen = definePage({
  id: 'scroll-preview',
  title: '滚动连续性验收',
  Component: View,
  presentation: { style: 'push', headerVariant: 'transparent' },
});
