import { t as currentTranslation } from '../i18n/index.ts';

/** Resolve product copy when rendering, while keeping user-provided titles literal. */
export type PageTitle = string | ((t: typeof currentTranslation) => string);

export function resolvePageTitle(
  title: PageTitle,
  t = currentTranslation,
): string {
  return typeof title === 'function' ? title(t) : title;
}
