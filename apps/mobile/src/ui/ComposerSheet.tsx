import { useState, type ComponentProps, type ReactNode } from 'react';
import { View } from 'react-native';
import { NativeGroupedList } from '@lody-ios/kit';

/** Keep the list beneath the floating input, including keyboard and draft growth. */
export function ComposerSheet({
  children,
  ...list
}: ComponentProps<typeof NativeGroupedList> & { children: ReactNode }) {
  const [bottomInset, setBottomInset] = useState(80);
  return (
    <View style={{ flex: 1 }}>
      <NativeGroupedList
        {...list}
        transparent
        style={{ flex: 1 }}
        bottomInset={bottomInset}
      />
      <View
        style={{ position: 'absolute', left: 0, right: 0, bottom: 0 }}
        onLayout={({ nativeEvent }) =>
          setBottomInset(nativeEvent.layout.height)
        }
      >
        {children}
      </View>
    </View>
  );
}
