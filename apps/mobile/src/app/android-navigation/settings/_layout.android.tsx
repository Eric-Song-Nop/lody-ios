import { Stack } from 'expo-router';
import { useColorScheme } from 'react-native';
export default function SettingsStack() {
  const dark = useColorScheme() === 'dark';
  return (
    <Stack
      screenOptions={{
        headerTransparent: false,
        statusBarStyle: dark ? 'light' : 'dark',
      }}
    >
      <Stack.Screen name="index" options={{ title: 'Settings' }} />
    </Stack>
  );
}
