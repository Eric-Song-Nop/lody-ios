import { Stack } from 'expo-router';
export default function ProjectsStack() {
  return (
    <Stack screenOptions={{ headerTransparent: false }}>
      <Stack.Screen name="index" options={{ title: 'Projects' }} />
    </Stack>
  );
}
