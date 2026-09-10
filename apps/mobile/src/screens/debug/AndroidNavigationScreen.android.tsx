import { useEffect, useState, type PropsWithChildren } from 'react';
import {
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  useColorScheme,
} from 'react-native';
import { router } from 'expo-router';
import { definePage, present } from '@/lib/presentation';
import { usePageRuntime } from '@/hooks/screens/usePageRuntime';
import {
  requestOpenSession,
  subscribeSessionNav,
} from '@/features/sessions/sessionNav';
import type { Session } from '@/models/catalog';
import { androidLocalesPage } from './AndroidLocalesScreen.android';
import { androidListsPage } from './AndroidListsScreen.android';
import { androidControlsPage } from './AndroidControlsScreen.android';
import { androidMenusPage } from './AndroidMenusScreen.android';
import { androidMenuEdgesPage } from './AndroidMenuEdgesScreen.android';
import {
  trackNavigationResult,
  useNavigationPageAudit,
} from '@/features/debug/androidNavigationAudit';

const fixtureSession: Session = {
  id: 'navigation-session',
  machineId: 'offline',
  projectId: 'navigation-project',
  title: 'Offline session',
  status: 'idle',
  archived: false,
  pinned: false,
  createdAt: '2026-09-10T00:00:00Z',
};
const pushPath = '/android-navigation/projects/presented/[presentationId]';

function Scene({ children }: PropsWithChildren) {
  useNavigationPageAudit();
  const dark = useColorScheme() === 'dark';
  return (
    <ScrollView
      style={{ backgroundColor: dark ? '#121212' : '#ffffff' }}
      contentContainerStyle={styles.scene}
    >
      {children}
    </ScrollView>
  );
}
function Copy({ children }: PropsWithChildren) {
  const dark = useColorScheme() === 'dark';
  return (
    <Text style={{ color: dark ? '#ffffff' : '#111111', fontSize: 18 }}>
      {children}
    </Text>
  );
}
function Action({ title, onPress }: { title: string; onPress: () => void }) {
  return (
    <Pressable
      accessibilityRole="button"
      onPress={onPress}
      android_ripple={{ color: '#ffffff33' }}
      style={styles.action}
    >
      <Text style={styles.actionText}>{title}</Text>
    </Pressable>
  );
}

function ProjectsScreen() {
  const [returns, setReturns] = useState(0);
  useEffect(
    () =>
      subscribeSessionNav(async (intent) => {
        if (intent.kind !== 'open')
          throw new Error('This offline scene only opens sessions');
        await trackNavigationResult(
          present(messagesPage, { session: intent.session }),
        );
      }),
    [],
  );
  return (
    <Scene>
      <Copy>Offline navigation: projects</Copy>
      <Copy>Project returns: {returns}</Copy>
      <Action
        title="Open offline project"
        onPress={() => {
          void trackNavigationResult(present(sessionsPage)).then(() =>
            setReturns((value) => value + 1),
          );
        }}
      />
      <Action
        title="Return to runtime verification"
        onPress={() => router.back()}
      />
      <Action
        title="Open native languages"
        onPress={() => {
          void present(androidLocalesPage, undefined, { style: 'push' });
        }}
      />
      <Action
        title="Open lists page"
        onPress={() => {
          void present(androidListsPage, undefined, { style: 'push' });
        }}
      />
      <Action
        title="Open menu edges page"
        onPress={() => {
          void present(androidMenuEdgesPage, undefined, { style: 'push' });
        }}
      />
      <Action
        title="Open menus page"
        onPress={() => {
          void present(androidMenusPage, undefined, { style: 'push' });
        }}
      />
      <Action
        title="Open controls page"
        onPress={() => {
          void present(androidControlsPage, undefined, { style: 'push' });
        }}
      />
    </Scene>
  );
}
function SessionsScreen() {
  return (
    <Scene>
      <Copy>Offline navigation: sessions</Copy>
      <Action
        title="Open offline session"
        onPress={() => {
          void requestOpenSession(fixtureSession);
        }}
      />
    </Scene>
  );
}
function MessagesScreen() {
  const { params } = usePageRuntime<{ session: Session }>();
  return (
    <Scene>
      <Copy>Offline navigation: messages</Copy>
      <Copy>{params.session.title}</Copy>
      <Copy>Deterministic transcript; no Cloud connection.</Copy>
    </Scene>
  );
}
function SettingsScreen() {
  const [result, setResult] = useState('No sheet result');
  const [settled, setSettled] = useState(0);
  const open = (style: 'formSheet' | 'pageSheet') => {
    void trackNavigationResult(present(sheetPage, undefined, { style })).then(
      (value) => {
        setResult(value.status);
        setSettled((count) => count + 1);
      },
    );
  };
  return (
    <Scene>
      <Copy>Offline navigation: settings</Copy>
      <Copy>Sheet result: {result}</Copy>
      <Copy>Settled sheets: {settled}</Copy>
      <Action title="Open form sheet" onPress={() => open('formSheet')} />
      <Action title="Open page sheet" onPress={() => open('pageSheet')} />
      <Action
        title="Open lists sheet"
        onPress={() => {
          void present(androidListsPage, undefined, {
            style: 'formSheet',
            sheetAllowedDetents: [1],
          });
        }}
      />
      <Action
        title="Open menu edges sheet"
        onPress={() => {
          void present(androidMenuEdgesPage, undefined, {
            style: 'formSheet',
            sheetAllowedDetents: [1],
          });
        }}
      />
      <Action
        title="Open menus sheet"
        onPress={() => {
          void present(androidMenusPage, undefined, {
            style: 'formSheet',
            sheetAllowedDetents: [1],
          });
        }}
      />
      <Action
        title="Open controls sheet"
        onPress={() => {
          void present(androidControlsPage, undefined, {
            style: 'formSheet',
            sheetAllowedDetents: [1],
          });
        }}
      />
    </Scene>
  );
}
function SheetScreen() {
  const runtime = usePageRuntime();
  const [childResult, setChildResult] = useState('none');
  return (
    <Scene>
      <Copy>Offline navigation: sheet</Copy>
      <Copy>Child result: {childResult}</Copy>
      <Action title="Complete sheet" onPress={() => runtime.finish()} />
      <Action title="Cancel sheet" onPress={runtime.cancel} />
      <Action
        title="Push sheet child"
        onPress={() => {
          void trackNavigationResult(runtime.push(childPage)).then((result) =>
            setChildResult(result.status),
          );
        }}
      />
    </Scene>
  );
}
function ChildScreen() {
  const runtime = usePageRuntime();
  return (
    <Scene>
      <Copy>Offline navigation: sheet child</Copy>
      <Action title="Complete child" onPress={() => runtime.finish()} />
      <Action
        title="Dismiss entire navigation"
        onPress={() => router.dismissAll()}
      />
    </Scene>
  );
}

export const projectsPage = definePage({
  id: 'android-navigation-projects',
  title: 'Projects',
  Component: ProjectsScreen,
});
export const settingsPage = definePage({
  id: 'android-navigation-settings',
  title: 'Settings',
  Component: SettingsScreen,
});
const sessionsPage = definePage({
  id: 'android-navigation-sessions',
  title: 'Sessions',
  Component: SessionsScreen,
  presentationPath: pushPath,
  presentation: { style: 'push' },
});
const messagesPage = definePage<{ session: Session }>({
  id: 'android-navigation-messages',
  title: 'Messages',
  Component: MessagesScreen,
  presentationPath: pushPath,
  presentation: { style: 'push' },
  parseRouteParams: () => {
    throw new Error('Session parameters belong to the presentation mailbox');
  },
});
const sheetPage = definePage({
  id: 'android-navigation-sheet',
  title: 'Navigation sheet',
  Component: SheetScreen,
  presentation: { style: 'formSheet', sheetAllowedDetents: [0.8] },
});
const childPage = definePage({
  id: 'android-navigation-child',
  title: 'Sheet child',
  Component: ChildScreen,
});
const styles = StyleSheet.create({
  scene: { padding: 24, gap: 20, flexGrow: 1 },
  action: {
    minHeight: 48,
    padding: 12,
    justifyContent: 'center',
    backgroundColor: '#1565c0',
    borderRadius: 4,
  },
  actionText: { color: '#ffffff', fontSize: 16 },
});
