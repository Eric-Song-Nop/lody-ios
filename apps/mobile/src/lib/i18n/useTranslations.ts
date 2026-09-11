import { useMemo, useSyncExternalStore } from 'react';
import { currentLocale, subscribeLocale, translationsFor } from './index.ts';

/** Subscribe at each translated view; changing locale must not remount routes. */
export function useTranslations() {
  const locale = useSyncExternalStore(
    subscribeLocale,
    currentLocale,
    currentLocale,
  );
  return useMemo(() => translationsFor(locale), [locale]);
}
