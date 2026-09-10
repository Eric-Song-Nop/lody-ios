import { Stack, ThemeProvider } from 'expo-router';
import { useColorScheme } from 'react-native';
import { nativePresentationOptions } from '@/lib/presentation';
import { navigationThemes } from '@/lib/theme/palette';
import { FeedbackBoundary } from '@/lib/presentation/FeedbackBoundary';
export default function AndroidLayout() {
  const theme =
    useColorScheme() === 'dark'
      ? navigationThemes.dark
      : navigationThemes.light;
  return (
    <ThemeProvider value={theme}>
      <FeedbackBoundary>
        <Stack
          screenOptions={{
            headerTransparent: false,
            statusBarStyle: theme.dark ? 'light' : 'dark',
          }}
        >
          <Stack.Screen
            name="index"
            options={{ headerShown: false, statusBarStyle: 'dark' }}
          />
          <Stack.Screen
            name="android-navigation"
            options={{ headerShown: false }}
          />
          <Stack.Screen
            name="presented/[presentationId]"
            options={({ route }) =>
              nativePresentationOptions(route.params, theme.colors.background)
            }
          />
        </Stack>
      </FeedbackBoundary>
    </ThemeProvider>
  );
}
