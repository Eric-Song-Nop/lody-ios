import { useEffect, useSyncExternalStore } from 'react';
import { useLocalSearchParams } from 'expo-router';
import {
  getPresentationSession,
  type PresentationResult,
} from '@/lib/presentation/presentationStore';

const listeners = new Set<() => void>();
const observedIds = new Set<number>();
let mounted = 0;
let pending = 0;
let settled = 0;
let cancelled = 0;

function notify() {
  for (const listener of listeners) listener();
}

function snapshot() {
  const retained = [...observedIds].filter((id) =>
    getPresentationSession(id),
  ).length;
  return `Navigation audit: mounted=${mounted} pending=${pending} retained=${retained} observed=${observedIds.size} settled=${settled} cancelled=${cancelled}`;
}

export function resetNavigationAudit() {
  if (
    mounted ||
    pending ||
    [...observedIds].some((id) => getPresentationSession(id))
  ) {
    throw new Error(
      'Navigation audit cannot reset while a previous host owns pages or sessions',
    );
  }
  observedIds.clear();
  settled = 0;
  cancelled = 0;
  notify();
}

export function useNavigationAudit() {
  return useSyncExternalStore(
    (listener) => {
      listeners.add(listener);
      return () => {
        listeners.delete(listener);
      };
    },
    snapshot,
    snapshot,
  );
}

export function useNavigationPageAudit() {
  const { presentationId } = useLocalSearchParams<{
    presentationId?: string;
  }>();
  useEffect(() => {
    mounted++;
    const id = Number(presentationId);
    if (Number.isSafeInteger(id) && id > 0) observedIds.add(id);
    notify();
    return () => {
      mounted--;
      notify();
    };
  }, [presentationId]);
}

export function trackNavigationResult<T>(
  promise: Promise<PresentationResult<T>>,
) {
  pending++;
  notify();
  return promise.then(
    (result) => {
      pending--;
      settled++;
      if (result.status === 'cancelled') cancelled++;
      notify();
      return result;
    },
    (error: unknown) => {
      pending--;
      notify();
      throw error;
    },
  );
}
