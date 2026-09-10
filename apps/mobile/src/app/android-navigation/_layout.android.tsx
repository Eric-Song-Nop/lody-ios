import { NativeTabs } from 'expo-router/unstable-native-tabs';
export default function AndroidNavigationTabs() {
  return (
    <NativeTabs tintColor="#1565c0">
      <NativeTabs.Trigger name="projects">
        <NativeTabs.Trigger.Label>Projects</NativeTabs.Trigger.Label>
      </NativeTabs.Trigger>
      <NativeTabs.Trigger name="settings">
        <NativeTabs.Trigger.Label>Settings</NativeTabs.Trigger.Label>
      </NativeTabs.Trigger>
    </NativeTabs>
  );
}
