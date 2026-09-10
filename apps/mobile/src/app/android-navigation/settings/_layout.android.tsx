import { Stack } from 'expo-router';
export default function SettingsStack() {
  return (
    <Stack screenOptions={{ headerTransparent: false }}>
      <Stack.Screen name="index" options={{ title: 'Settings' }} />
    </Stack>
  );
}
