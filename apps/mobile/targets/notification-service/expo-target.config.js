module.exports = (config) => ({
  type: 'notification-service',
  name: 'LodyNotificationService',
  bundleIdentifier: '.notification-service',
  deploymentTarget: '16.4',
  entitlements: {
    'com.apple.security.application-groups':
      config.ios.entitlements['com.apple.security.application-groups'],
  },
});
