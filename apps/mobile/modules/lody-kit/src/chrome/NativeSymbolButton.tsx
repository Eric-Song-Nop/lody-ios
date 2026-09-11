import { requireNativeView } from 'expo';
import type { ComponentType } from 'react';
import { Platform, type ViewProps } from 'react-native';

export interface NativeSymbolButtonProps extends ViewProps {
  accessibilityName: string;
  symbol: string;
  prominent?: boolean;
  disabled?: boolean;
  tint?: string;
  onPress: () => void;
  onLongPress?: () => void;
}

const NativeView: ComponentType<
  Omit<NativeSymbolButtonProps, 'onPress' | 'onLongPress'> & {
    longPress?: boolean;
    onSymbolPress: () => void;
    onSymbolLongPress?: () => void;
  }
> = requireNativeView('LodyKit', 'LodySymbolButton');

export function NativeSymbolButton({
  onPress,
  onLongPress,
  style,
  ...props
}: NativeSymbolButtonProps) {
  return (
    <NativeView
      {...props}
      style={[
        style,
        Platform.OS === 'android' && { minWidth: 48, minHeight: 48 },
      ]}
      longPress={!!onLongPress}
      onSymbolPress={onPress}
      onSymbolLongPress={onLongPress}
    />
  );
}
