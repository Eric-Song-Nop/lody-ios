const { withGradleProperties } = require('expo/config-plugins');

module.exports = function withAndroidBuild(config) {
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
