import type { ExpoConfig } from 'expo/config';

const config: ExpoConfig = {
  name: 'Lody',
  slug: 'lody-ios',
  version: '0.1.0',
  platforms: ['ios'],
  scheme: 'lody-ios',
  orientation: 'portrait',
  userInterfaceStyle: 'automatic',
  icon: './assets/icon.png',
  ios: {
    bundleIdentifier: 'app.innei.lody',
    appleTeamId: 'KAMM5N88X3',
    supportsTablet: false,
    config: { usesNonExemptEncryption: false },
    entitlements: {
      'aps-environment': 'production',
      'com.apple.security.application-groups': ['group.app.innei.lody'],
    },
    infoPlist: {
      BGTaskSchedulerPermittedIdentifiers: ['app.innei.lody.session-sync.*'],
      UIBackgroundModes: ['processing'],
    },
  },
  plugins: [
    'expo-router',
    ['expo-dev-client', { toolsButton: false }],
    './plugins/withMarkdownView',
    './plugins/withLocales',
    'expo-localization',
    '@bacons/apple-targets',
  ],
  experiments: { typedRoutes: true, reactCompiler: true },
  runtimeVersion: { policy: 'fingerprint' },
  updates: {
    url: 'https://ota.innei.in/manifest',
    enabled: true,
    fallbackToCacheTimeout: 0,
    requestHeaders: {
      'expo-channel-name': 'production',
      'expo-app-id': 'lody',
    },
  },
};

export default config;
