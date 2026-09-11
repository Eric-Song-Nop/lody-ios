import type { PropsWithChildren } from 'react';
import { NativeFeedbackHost } from '@lody-ios/kit';

export function FeedbackBoundary({ children }: PropsWithChildren) {
  return (
    <>
      {children}
      <NativeFeedbackHost />
    </>
  );
}
