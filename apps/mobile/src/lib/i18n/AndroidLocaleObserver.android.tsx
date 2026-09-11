import { getLocales, useLocales } from 'expo-localization';
import { useEffect } from 'react';
import { AppState } from 'react-native';
import { matchLocale, setLocale } from './index.ts';

function refreshLocale() {
  setLocale(matchLocale(getLocales()[0]?.languageTag));
}

/** One lifecycle owner, independent of navigation and presentation sessions. */
export function AndroidLocaleObserver() {
  const locales = useLocales();
  useEffect(refreshLocale, [locales]);
  useEffect(() => {
    const subscription = AppState.addEventListener('change', (state) => {
      if (state === 'active') refreshLocale();
    });
    // Read again after subscribing so a change during mounting is not missed.
    refreshLocale();
    return () => subscription.remove();
  }, []);
  return null;
}
