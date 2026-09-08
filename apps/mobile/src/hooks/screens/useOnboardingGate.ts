import { useEffect, useRef, useState } from 'react';
import { useAuth } from '@/cloud/auth/AuthProvider';
import { present } from '@/lib/presentation';
import { OnboardingScreen } from '@/screens/OnboardingScreen';

export function useOnboardingGate() {
  const { account, localReady } = useAuth();
  const presenting = useRef(false);
  const [attempt, setAttempt] = useState(0);
  useEffect(() => {
    if (!localReady || account || presenting.current) return;
    presenting.current = true;
    present(OnboardingScreen).then(
      (result) => {
        presenting.current = false;
        if (result.status === 'cancelled') setAttempt((n) => n + 1);
      },
      () => {
        presenting.current = false;
      },
    );
  }, [account, localReady, attempt]);
}
