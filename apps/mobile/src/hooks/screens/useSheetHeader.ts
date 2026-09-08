import { use, useEffect } from 'react';
import {
  SheetHeaderContext,
  type HeaderItems,
} from '@/lib/presentation/SheetStack';

export function useSheetHeader(items: HeaderItems, left?: HeaderItems) {
  const setItems = use(SheetHeaderContext);
  useEffect(() => {
    setItems?.({ right: items, left });
    return () => setItems?.(undefined);
  }, [setItems, items, left]);
}
