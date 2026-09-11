import { requireNativeView } from 'expo';
import { type ComponentType, useState } from 'react';
import {
  Platform,
  type NativeSyntheticEvent,
  type ViewProps,
} from 'react-native';

export type NativeMenuItem = {
  id: string;
  title: string;
  symbol?: string;
  selected?: boolean;
};

export interface NativeMenuButtonProps extends ViewProps {
  accessibilityName: string;
  avatar: { text: string; color: string };
  label: string;
  items: NativeMenuItem[];
  onSelect: (id: string) => void;
}

const NativeView: ComponentType<
  Omit<NativeMenuButtonProps, 'onSelect'> & {
    onSelect: (event: NativeSyntheticEvent<{ id: string }>) => void;
    onSize: (event: NativeSyntheticEvent<{ width: number }>) => void;
  }
> = requireNativeView('LodyKit', 'LodyMenuButton');

export function NativeMenuButton({
  onSelect,
  style,
  ...props
}: NativeMenuButtonProps) {
  const [width, setWidth] = useState(Platform.OS === 'android' ? 48 : 44);
  return (
    <NativeView
      {...props}
      style={[
        { width, height: Platform.OS === 'android' ? 48 : 44 },
        style,
        Platform.OS === 'android' && { minWidth: 48, minHeight: 48 },
      ]}
      onSelect={({ nativeEvent }) => onSelect(nativeEvent.id)}
      onSize={({ nativeEvent }) => setWidth(Math.ceil(nativeEvent.width))}
    />
  );
}
