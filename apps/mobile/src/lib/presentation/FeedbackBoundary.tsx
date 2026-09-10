import type { PropsWithChildren } from 'react';

// iOS already owns an independent UIKit feedback window.
export function FeedbackBoundary({ children }: PropsWithChildren) {
  return children;
}
