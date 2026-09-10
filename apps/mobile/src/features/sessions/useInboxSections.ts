import { useMemo } from 'react';
import type { Catalog } from '../../models/catalog';
import { useTranslations } from '../../lib/i18n/useTranslations';
import { inboxSections, projectSections } from './inbox';

/** Language changes refresh display projections without replacing catalog state. */
export function useInboxSections(
  catalog: Catalog,
  mode: number,
  accent: string,
  expanded: Record<string, boolean>,
) {
  const { locale } = useTranslations();
  return useMemo(
    () =>
      mode === 0
        ? projectSections(catalog, accent, expanded)
        : inboxSections(catalog, { accent }),
    [catalog, mode, accent, expanded, locale],
  );
}
