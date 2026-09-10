import type { ExpoConfig } from 'expo/config';

const config: ExpoConfig = {
  name: 'Lody',
  slug: 'lody-ios',
  version: '0.1.0',
  platforms: ['ios', 'android'],
  android: { package: 'app.innei.lody' },
  scheme: 'lody-ios',
  orientation: 'portrait',
  userInterfaceStyle: 'automatic',
  icon: './assets/icon.png',
  ios: {
    bundleIdentifier: 'app.innei.lody',
    appleTeamId: 'KAMM5N88X3',
    supportsTablet: false,
    config: { usesNonExemptEncryption: false },
    infoPlist: {
      BGTaskSchedulerPermittedIdentifiers: ['app.innei.lody.session-sync.*'],
      UIBackgroundModes: ['processing'],
    },
  },
  plugins: [
    'expo-router',
    ['expo-dev-client', { toolsButton: false }],
    './plugins/withMarkdownView',
    './plugins/withAndroidBuild',
    './plugins/withLocales',
    'expo-localization',
    [
      './plugins/withPushNotifications',
      {
        appId:
          process.env.LODY_ONESIGNAL_APP_ID ??
          'e383bf31-7c8e-4641-b3f6-3486e77b9a82',
      },
    ],
  ],
  experiments: { typedRoutes: true, reactCompiler: true },
  runtimeVersion: { policy: 'fingerprint' },
  updates: {
    url: 'https://ota.innei.in/manifest',
    enabled: process.env.EXPO_PUBLIC_ANDROID_VERIFY !== '1',
    fallbackToCacheTimeout: 0,
    requestHeaders: {
      'expo-channel-name': 'production',
      'expo-app-id': 'lody',
    },
  },
};

export default config;
