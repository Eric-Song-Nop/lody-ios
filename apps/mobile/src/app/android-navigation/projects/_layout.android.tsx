import { Stack } from 'expo-router';
import { useColorScheme } from 'react-native';
import { nativePresentationOptions } from '@/lib/presentation';
import { navigationThemes } from '@/lib/theme/palette';
export default function ProjectsStack() {
  const theme =
    useColorScheme() === 'dark'
      ? navigationThemes.dark
      : navigationThemes.light;
  return (
    <Stack screenOptions={{ headerTransparent: false }}>
      <Stack.Screen name="index" options={{ title: 'Projects' }} />
      <Stack.Screen
        name="presented/[presentationId]"
        options={({ route }) =>
          nativePresentationOptions(route.params, theme.colors.background)
        }
      />
    </Stack>
  );
}
