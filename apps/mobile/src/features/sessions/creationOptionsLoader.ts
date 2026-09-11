import { createContext } from 'react';
import type { CreationOptions } from '@/models/send';

/** Optional service boundary for offline hosts; production uses the native runtime. */
export const CreationOptionsLoaderContext = createContext<
  ((projectId: string) => Promise<CreationOptions>) | undefined
>(undefined);
