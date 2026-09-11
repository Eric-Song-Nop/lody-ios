import en from '../../../locales/en.json' with { type: 'json' };
import zhHans from '../../../locales/zh-Hans.json' with { type: 'json' };
import type { Locale, TemplateVars } from './format.ts';
import { formatTemplate, pluralSuffix } from './format.ts';

export type { Locale, TemplateVars } from './format.ts';
export { matchLocale } from './format.ts';

export type TranslationKey = keyof typeof zhHans;

type PluralBase<K> = K extends `${infer Base}.one`
  ? `${Base}.other` extends TranslationKey
    ? Base
    : never
  : never;

export type PluralKey = PluralBase<TranslationKey>;

const catalogs: Record<Locale, Record<TranslationKey, string>> = {
  'zh-Hans': zhHans,
  en,
};
const translators = {
  en: createTranslations('en'),
  'zh-Hans': createTranslations('zh-Hans'),
};

let locale: Locale = 'en';
const listeners = new Set<() => void>();

/** Initialize before routes load; subsequent changes notify subscribed views. */
export function setLocale(next: Locale) {
  if (locale === next) return;
  locale = next;
  for (const listener of [...listeners]) listener();
}

export function subscribeLocale(listener: () => void) {
  listeners.add(listener);
  return () => {
    listeners.delete(listener);
  };
}

export function currentLocale() {
  return locale;
}

export function t(key: TranslationKey, vars?: TemplateVars) {
  return translationsFor(locale).t(key, vars);
}

export function tp(key: PluralKey, count: number, vars?: TemplateVars) {
  return translationsFor(locale).tp(key, count, vars);
}

/** Bind render-time copy to one snapshot, including memoized callbacks. */
export function translationsFor(language: Locale) {
  return translators[language];
}

function createTranslations(language: Locale) {
  const catalog = catalogs[language];
  return {
    locale: language,
    t(key: TranslationKey, vars?: TemplateVars) {
      return formatTemplate(catalog[key] ?? key, vars);
    },
    tp(key: PluralKey, count: number, vars?: TemplateVars) {
      const exact = `${key}${pluralSuffix(language, count)}` as TranslationKey;
      const template =
        catalog[exact] ?? catalog[`${key}.other` as TranslationKey];
      return formatTemplate(template ?? key, vars);
    },
  };
}
