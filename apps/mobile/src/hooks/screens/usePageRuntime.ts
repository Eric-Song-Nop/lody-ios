import { use } from 'react';
import { PageRuntimeContext, type PageRuntime } from '@/lib/presentation/page';

export function usePageRuntime<
  TParams = undefined,
  TResult = void,
>(): PageRuntime<TParams, TResult> {
  const runtime = use(PageRuntimeContext);
  if (!runtime) {
    throw new Error(
      'usePageRuntime must be used inside a Page route or presentation session.',
    );
  }
  return runtime as PageRuntime<TParams, TResult>;
}
