import { requireNativeView } from 'expo';
import type { ComponentType } from 'react';
import type { ViewProps } from 'react-native';

const NativeView: ComponentType<ViewProps> = requireNativeView(
  'LodyKit',
  'LodyFeedbackHost',
);

/** A window registration marker; all visible feedback is owned by Kotlin. */
export function NativeFeedbackHost() {
  return (
    <NativeView
      pointerEvents="none"
      accessible={false}
      style={{ position: 'absolute', top: 0, left: 0, width: 1, height: 1 }}
    />
  );
}
