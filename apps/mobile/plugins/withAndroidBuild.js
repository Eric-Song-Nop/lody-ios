const {
  AndroidConfig,
  withAndroidManifest,
  withGradleProperties,
} = require('expo/config-plugins');

module.exports = function withAndroidBuild(config) {
  config = withAndroidManifest(config, (config) => {
    const activity = AndroidConfig.Manifest.getMainActivityOrThrow(
      config.modResults,
    );
    const changes = new Set(
      (activity.$['android:configChanges'] ?? '').split('|').filter(Boolean),
    );
    // Keep the active route/draft while RN and native views handle font changes.
    changes.add('fontScale');
    activity.$['android:configChanges'] = [...changes].join('|');
    return config;
  });
  return withGradleProperties(config, (config) => {
    const values = {
      'org.gradle.jvmargs': '-Xmx4096m -XX:MaxMetaspaceSize=2048m',
      'org.gradle.workers.max': '4',
    };
    for (const [key, value] of Object.entries(values)) {
      const property = config.modResults.find(
        (item) => item.type === 'property' && item.key === key,
      );
      if (property) property.value = value;
      else config.modResults.push({ type: 'property', key, value });
    }
    return config;
  });
};
