import { registerRootComponent } from 'expo';
import { useEffect, useState } from 'react';
import { Button, StyleSheet, Text, View } from 'react-native';
import { SafeAreaProvider, SafeAreaView } from 'react-native-safe-area-context';
import { addAppActiveListener, runtimeInfo } from '@lody-ios/kit';

if (process.env.EXPO_PUBLIC_ANDROID_VERIFY !== '1') {
  throw new Error(
    'Android product entry is not available. Use the internal verification build.',
  );
}

function BootstrapProbe() {
  const [subscribed, setSubscribed] = useState(true);
  const [events, setEvents] = useState(0);
  useEffect(() => {
    if (!subscribed) return;
    const subscription = addAppActiveListener(() =>
      setEvents((count) => count + 1),
    );
    return () => subscription.remove();
  }, [subscribed]);
  return (
    <SafeAreaView style={styles.page}>
      <View style={styles.content}>
        <Text accessibilityRole="header" style={styles.title}>
          Lody Android verification
        </Text>
        <Text>Internal bootstrap · PR-01</Text>
        <Text testID="native-runtime">
          {runtimeInfo.moduleName}: {runtimeInfo.systemVersion}
        </Text>
        <Text testID="lifecycle-count">Foreground events: {events}</Text>
        <Text testID="lifecycle-state">
          {subscribed ? 'Listener attached' : 'Listener detached'}
        </Text>
        <Button
          title={subscribed ? 'Detach listener' : 'Attach listener'}
          onPress={() => setSubscribed((value) => !value)}
        />
      </View>
    </SafeAreaView>
  );
}
function AndroidVerification() {
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
});
registerRootComponent(AndroidVerification);
