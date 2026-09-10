import { Text, type TextProps } from 'react-native';
import { usePalette, type ColorRole } from '@/lib/theme/palette';
import type { TypeRole } from '@/lib/theme/tokens';

export type AppTextProps = Omit<TextProps, 'allowFontScaling'> & {
  variant?: TypeRole;
};
const roles: Record<
  TypeRole,
  { color: ColorRole; size: number; line: number }
> = {
  title: { color: 'label', size: 22, line: 28 },
  body: { color: 'label', size: 16, line: 24 },
  secondary: { color: 'secondaryLabel', size: 14, line: 20 },
  meta: { color: 'secondaryLabel', size: 12, line: 16 },
  eyebrow: { color: 'secondaryLabel', size: 12, line: 16 },
  mono: { color: 'label', size: 14, line: 20 },
};

export function AppText({ variant = 'body', style, ...props }: AppTextProps) {
  const palette = usePalette();
  const role = roles[variant];
  return (
    <Text
      {...props}
      allowFontScaling
      style={[
        {
          color: palette[role.color],
          fontSize: role.size,
          lineHeight: role.line,
          fontFamily: variant === 'mono' ? 'monospace' : undefined,
          fontWeight: variant === 'title' ? '500' : undefined,
        },
        style,
      ]}
    />
  );
}
