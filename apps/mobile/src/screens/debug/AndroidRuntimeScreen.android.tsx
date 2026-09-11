import { router } from 'expo-router';
import { useEffect, useState } from 'react';
import { Pressable, StyleSheet, Text, ScrollView } from 'react-native';
import { SafeAreaProvider, SafeAreaView } from 'react-native-safe-area-context';
import {
  addAppActiveListener,
  runtimeInfo,
  runDataRuntimeVerification,
  runRuntimeRecoveryVerification,
  addRecoveryPhaseListener,
  runStorageVerification,
} from '@lody-ios/kit';
import {
  resetNavigationAudit,
  useNavigationAudit,
} from '@/features/debug/androidNavigationAudit';

if (process.env.EXPO_PUBLIC_ANDROID_VERIFY !== '1') {
  throw new Error(
    'Android product entry is not available. Use the internal verification build.',
  );
}

function ProbeButton({
  title,
  onPress,
  disabled = false,
}: {
  title: string;
  onPress: () => void;
  disabled?: boolean;
}) {
  return (
    <Pressable
      accessibilityRole="button"
      accessibilityState={{ disabled }}
      disabled={disabled}
      onPress={onPress}
      android_ripple={{ color: '#ffffff33' }}
      style={[styles.button, disabled && styles.disabled]}
    >
      <Text style={styles.buttonText}>{title.toUpperCase()}</Text>
    </Pressable>
  );
}

function BootstrapProbe() {
  const navigationAudit = useNavigationAudit();
  const [subscribed, setSubscribed] = useState(true);
  const [events, setEvents] = useState(0);
  const [wasm, setWasm] = useState('WASM not run');
  const [recovery, setRecovery] = useState('Recovery not run');
  const [storage, setStorage] = useState('Storage not run');
  const [running, setRunning] = useState(false);
  useEffect(() => {
    const subscription = addRecoveryPhaseListener(({ phase }) =>
      setRecovery(phase),
    );
    return () => subscription.remove();
  }, []);
  async function verifyStorage() {
    setRunning(true);
    setStorage('Storage running');
    try {
      let report = JSON.parse(await runStorageVerification());
      if (report.status === 'needs_runtime') {
        setStorage('Storage running: real WASM seed');
        const wasmReport = JSON.parse(await runDataRuntimeVerification());
        if (typeof wasmReport.verifiedCatalog !== 'string')
          throw new Error('Missing verified runtime catalog');
        report = JSON.parse(
          await runStorageVerification(wasmReport.verifiedCatalog),
        );
      }
      setStorage(
        report.status === 'prepared'
          ? 'Storage prepared: restart required'
          : `Storage passed: ${report.cases.length} cases`,
      );
    } catch (error) {
      setStorage(
        `Storage failed: ${error instanceof Error ? error.message : 'unknown'}`,
      );
    } finally {
      setRunning(false);
    }
  }
  async function verifyRecovery() {
    setRunning(true);
    setWasm('WASM not run');
    setRecovery('Recovery running');
    try {
      const report = JSON.parse(await runRuntimeRecoveryVerification());
      setRecovery(`Recovery passed: ${report.cases.length} cases`);
    } catch (error) {
      setRecovery(
        `Recovery failed: ${error instanceof Error ? error.message : 'unknown'}`,
      );
    } finally {
      setRunning(false);
    }
  }
  async function verifyWasm() {
    setRunning(true);
    setWasm('WASM running');
    try {
      const report = JSON.parse(await runDataRuntimeVerification());
      setWasm(
        `WASM passed: ${report.cases.length} cases\n${report.cases.map((item: { name: string }) => item.name).join('\n')}`,
      );
    } catch (error) {
      setWasm(
        `WASM failed: ${error instanceof Error ? error.message : 'unknown'}`,
      );
    } finally {
      setRunning(false);
    }
  }
  useEffect(() => {
    if (!subscribed) return;
    const subscription = addAppActiveListener(() =>
      setEvents((count) => count + 1),
    );
    return () => subscription.remove();
  }, [subscribed]);
  return (
    <SafeAreaView style={styles.page}>
      <ScrollView contentContainerStyle={styles.content}>
        <Text accessibilityRole="header" style={styles.title}>
          Lody Android verification
        </Text>
        <Text>Internal native verification · PR-01/02/03/04</Text>
        <Text testID="native-runtime">
          {runtimeInfo.moduleName}: {runtimeInfo.systemVersion}
        </Text>
        <Text testID="lifecycle-count">Foreground events: {events}</Text>
        <Text testID="lifecycle-state">
          {subscribed ? 'Listener attached' : 'Listener detached'}
        </Text>
        <ProbeButton
          title={subscribed ? 'Detach listener' : 'Attach listener'}
          onPress={() => setSubscribed((value) => !value)}
        />
        <ProbeButton
          title="Run WASM verification"
          disabled={running}
          onPress={verifyWasm}
        />
        <ProbeButton
          title="Run recovery verification"
          disabled={running}
          onPress={verifyRecovery}
        />
        <ProbeButton
          title="Run storage verification"
          disabled={running}
          onPress={verifyStorage}
        />
        <ProbeButton
          title="Open navigation verification"
          onPress={() => {
            resetNavigationAudit();
            router.push('/android-navigation/projects' as never);
          }}
        />
        <Text>{navigationAudit}</Text>
        <Text testID="storage-result">{storage}</Text>
        <Text testID="recovery-result">{recovery}</Text>
        <Text testID="wasm-result">{wasm}</Text>
      </ScrollView>
    </SafeAreaView>
  );
}
export default function AndroidRuntimeScreen() {
  return (
    <SafeAreaProvider>
      <BootstrapProbe />
    </SafeAreaProvider>
  );
}
const styles = StyleSheet.create({
  page: { flex: 1, backgroundColor: '#f5f5f5' },
  content: { padding: 24, gap: 20 },
  title: { fontSize: 24, color: '#111111' },
  button: {
    minHeight: 48,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#1565c0',
    borderRadius: 4,
    padding: 12,
  },
  buttonText: { color: '#ffffff', fontSize: 16, fontWeight: '600' },
  disabled: { opacity: 0.5 },
});
