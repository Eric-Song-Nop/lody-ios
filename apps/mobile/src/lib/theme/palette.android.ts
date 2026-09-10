import { PlatformColor, useColorScheme } from 'react-native';
import { DarkTheme, DefaultTheme } from 'expo-router';

export type ColorRole =
  | 'label'
  | 'secondaryLabel'
  | 'tertiaryLabel'
  | 'accent'
  | 'warning'
  | 'danger'
  | 'background'
  | 'reading'
  | 'card'
  | 'inset'
  | 'separator'
  | 'fill'
  | 'onAccent';

const colors = {
  light: {
    accent: '#1565C0',
    onAccent: '#FFFFFF',
    background: '#F5F5F5',
    card: '#FFFFFF',
    text: '#1B1B1B',
    border: '#C6C6C6',
    danger: '#BA1A1A',
    warning: '#855400',
    inset: '#EEEEEE',
  },
  dark: {
    accent: '#90CAF9',
    onAccent: '#10243A',
    background: '#121212',
    card: '#252525',
    text: '#EEEEEE',
    border: '#555555',
    danger: '#FFB4AB',
    warning: '#FFCC80',
    inset: '#303030',
  },
} as const;

export function usePalette() {
  const theme = useColorScheme() === 'dark' ? 'dark' : 'light';
  const value = colors[theme];
  return {
    theme,
    // RN's theme-attribute converter returns TypedValue.data, which is a
    // resource ID for ColorStateLists. Resource paths resolve the actual color.
    label: PlatformColor(`@android:color/primary_text_${theme}`),
    secondaryLabel: PlatformColor(`@android:color/secondary_text_${theme}`),
    tertiaryLabel: PlatformColor(`@android:color/secondary_text_${theme}`),
    accent: value.accent,
    warning: value.warning,
    danger: value.danger,
    background: value.background,
    reading: value.card,
    card: value.card,
    inset: value.inset,
    separator: value.border,
    fill: value.inset,
    onAccent: value.onAccent,
  } as const;
}
export type Palette = ReturnType<typeof usePalette>;

function navigationTheme(theme: 'light' | 'dark') {
  const base = theme === 'dark' ? DarkTheme : DefaultTheme;
  const value = colors[theme];
  return {
    ...base,
    colors: {
      ...base.colors,
      primary: value.accent,
      background: value.background,
      card: value.card,
      text: value.text,
      border: value.border,
      notification: value.danger,
    },
  };
}
export const navigationThemes = {
  light: navigationTheme('light'),
  dark: navigationTheme('dark'),
};
