import { useCallback, useRef } from 'react';
import { NativeGroupedList } from '@lody-ios/kit';
import { usePageRuntime } from '@/hooks/screens/usePageRuntime';
import { definePage } from '@/lib/presentation';
import {
  RemoteSettingsView,
  settingsTitle,
  type SettingsService,
} from '../RemoteSettingsScreen';
import type { RemoteSetting } from '@/models/settings';
import { t } from '../../lib/i18n/index.ts';

function View() {
  const { push } = usePageRuntime();
  const rows = useRef<RemoteSetting[]>([
    { kind: 'machine', id: 'm1', name: 'Studio Mac', detail: 'macOS' },
    {
      kind: 'agent',
      id: 'a1',
      machineId: 'm1',
      name: 'Codex',
      prompt: 'Keep changes focused.',
      detail: 'codex',
    },
    {
      kind: 'mcp',
      id: 'c1',
      name: 'Documentation',
      detail: 'http',
      enabledByDefault: false,
    },
  ]);
  const failLoad = useRef(true),
    failSave = useRef(true);
  const service = useCallback<SettingsService>(async (request) => {
    if (!__DEV__) throw new Error('Development only');
    if (failLoad.current) {
      failLoad.current = false;
      throw new Error(t('settings.remote.loadFailed'));
    }
    if (request.edit) {
      if (request.kind === 'agent' && failSave.current) {
        failSave.current = false;
        throw new Error(t('settings.remote.saveFailed'));
      }
      const edit = request.edit;
      rows.current = rows.current.map((row) =>
        row.id === edit.item.id
          ? {
              ...row,
              name: edit.name.trim(),
              ...(request.kind === 'agent' ? { prompt: edit.prompt } : {}),
              ...(request.kind === 'mcp'
                ? { enabledByDefault: edit.enabledByDefault }
                : {}),
            }
          : row,
      );
    }
    return rows.current.filter((row) => row.kind === request.kind);
  }, []);
  return (
    <NativeGroupedList
      style={{ flex: 1 }}
      sections={[
        {
          id: 'remote',
          rows: (['machine', 'agent', 'mcp'] as const).map((kind) => ({
            id: `settings-${kind}`,
            title: settingsTitle(kind),
            disclosure: true,
            action: true,
            navigates: true,
          })),
        },
      ]}
      onRowPress={({ nativeEvent: { id } }) => {
        const kind = id.slice('settings-'.length);
        if (kind !== 'machine' && kind !== 'agent' && kind !== 'mcp') return;
        void push(
          SettingsListPreviewScreen,
          { kind, service },
          { title: settingsTitle(kind) },
        );
      }}
    />
  );
}

const SettingsListPreviewScreen = definePage<{
  kind: RemoteSetting['kind'];
  service: SettingsService;
}>({
  id: 'settings-list-preview',
  title: (t) => t('settings.remote.title'),
  Component: () => {
    const { params } = usePageRuntime<{
      kind: RemoteSetting['kind'];
      service: SettingsService;
    }>();
    return <RemoteSettingsView {...params} workspaceId="offline-settings" />;
  },
  parseRouteParams: () => {
    throw new Error('Open from settings preview');
  },
  presentation: { style: 'push', headerVariant: 'transparent' },
});

export const SettingsPreviewScreen = definePage({
  id: 'settings-preview',
  title: (t) => t('settings.remote.title'),
  presentation: { headerVariant: 'transparent' },
  Component: View,
});
