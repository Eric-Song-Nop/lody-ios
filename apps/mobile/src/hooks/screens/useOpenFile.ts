import { useEffect, useRef } from 'react';
import { readFile, previewContent, showToast } from '@lody-ios/kit';
import { basename } from '@/features/sessions/path';
import { t, type TranslationKey } from '@/lib/i18n';
import { usePageRuntime } from './usePageRuntime';

const errors: Record<string, TranslationKey> = {
  too_large: 'files.error.tooLarge',
  file_not_found: 'files.error.notFound',
  permission_denied: 'files.error.permissionDenied',
  path_not_allowed: 'files.error.pathNotAllowed',
  decode_error: 'files.error.decode',
};

export function useOpenFile(sessionId: string) {
  const { push } = usePageRuntime();
  const busy = useRef(false);
  const active = useRef(true);
  useEffect(() => {
    active.current = true;
    return () => {
      active.current = false;
    };
  }, [sessionId]);
  return async (path: string, line?: number) => {
    if (busy.current || !sessionId) return;
    busy.current = true;
    try {
      const file = await readFile({ sessionId, path });
      if (!active.current) return;
      if (file.status !== 'ok') {
        const key = errors[file.code];
        showToast(key ? t(key) : (file.message ?? t('files.error.read')));
        return;
      }
      if (file.kind === 'image' || file.kind === 'binary') {
        await previewContent(file.handle);
      } else {
        const { FileScreen } = await import('@/screens/FileScreen');
        if (!active.current) return;
        void push(
          FileScreen,
          {
            path: file.path,
            handle: file.handle,
            bytes: file.bytes,
            sessionId,
            line,
          },
          { title: basename(file.path) },
        );
      }
    } catch {
      if (active.current) showToast(t('files.error.offline'));
    } finally {
      busy.current = false;
    }
  };
}
