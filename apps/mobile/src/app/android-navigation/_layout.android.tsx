import { NativeTabs } from 'expo-router/unstable-native-tabs';
import { usePalette } from '@/lib/theme/palette';
export default function AndroidNavigationTabs() {
  const colors = usePalette();
  return (
    <NativeTabs
      tintColor={colors.accent}
      backgroundColor={colors.card}
      indicatorColor={colors.inset}
      iconColor={{ default: colors.secondaryLabel, selected: colors.accent }}
    >
      <NativeTabs.Trigger name="projects">
        <NativeTabs.Trigger.Icon
          drawable={{ default: 'lody_folder_outline', selected: 'lody_folder' }}
        />
        <NativeTabs.Trigger.Label>Projects</NativeTabs.Trigger.Label>
      </NativeTabs.Trigger>
      <NativeTabs.Trigger name="settings">
        <NativeTabs.Trigger.Icon
          drawable={{
            default: 'lody_settings_outline',
            selected: 'lody_settings',
          }}
        />
        <NativeTabs.Trigger.Label>Settings</NativeTabs.Trigger.Label>
      </NativeTabs.Trigger>
    </NativeTabs>
  );
}
