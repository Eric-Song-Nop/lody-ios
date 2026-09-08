import { useEffect } from 'react';
import { usePathname, useRouter } from 'expo-router';
import { addDebugShakeListener } from '@lody-ios/kit';
import { uiVerify } from '@/screens/debug/uiVerify';

export function useDebugShake() {
  const router = useRouter();
  const pathname = usePathname();
  useEffect(() => {
    if (uiVerify) return;
    const subscription = addDebugShakeListener(() => {
      if (pathname === '/debug') return;
      router.push('/debug');
    });
    return () => subscription.remove();
  }, [pathname, router]);
}
