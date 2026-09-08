import { requireNativeView } from 'expo';
import type { ComponentType } from 'react';
import type { ViewProps } from 'react-native';

export interface NativeSymbolProps extends ViewProps {
  symbol: string;
  pointSize?: number;
  tint?: string;
}

export const NativeSymbol: ComponentType<NativeSymbolProps> = requireNativeView(
  'LodyKit',
  'LodySymbolView',
);
