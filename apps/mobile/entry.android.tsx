import './src/lib/i18n/boot';
import { registerRootComponent } from 'expo';
import { ExpoRoot } from 'expo-router';
import type { ComponentProps } from 'react';

declare const require: NodeRequire & {
  context(
    directory: string,
    recursive: boolean,
    pattern: RegExp,
  ): ComponentProps<typeof ExpoRoot>['context'];
};

if (process.env.EXPO_PUBLIC_ANDROID_VERIFY !== '1') {
  throw new Error(
    'Android product entry is not available. Use the internal verification build.',
  );
}

// Only implemented Android routes enter Metro's graph during staged delivery.
const androidContext = require.context('./src/app', true, /\.android\.tsx$/);
// The platform has already been selected by Metro's filter. Router expects
// ordinary route keys, including a non-platform entry for every route.
const sourceKey = (key: string) => key.replace(/\.tsx$/, '.android.tsx');
const context = Object.assign((key: string) => androidContext(sourceKey(key)), {
  keys: () =>
    androidContext.keys().map((key) => key.replace(/\.android\.tsx$/, '.tsx')),
  resolve: (key: string) => androidContext.resolve(sourceKey(key)),
  id: androidContext.id,
});
function AndroidEntry() {
  return <ExpoRoot context={context} />;
}
registerRootComponent(AndroidEntry);
