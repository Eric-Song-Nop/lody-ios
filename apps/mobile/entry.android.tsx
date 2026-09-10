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
const context = require.context('./src/app', true, /\.android\.tsx$/);
function AndroidEntry() {
  return <ExpoRoot context={context} />;
}
registerRootComponent(AndroidEntry);
