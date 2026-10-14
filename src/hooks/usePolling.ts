import { useEffect, useRef, useState } from "react";

/**
 * Calls `fn` every `intervalMs` while `enabled`. Calls are chained with setTimeout,
 * so a slow backend never causes overlapping requests.
 */
export function usePolling<T>(
  fn: () => Promise<T>,
  intervalMs: number,
  enabled: boolean,
  deps: unknown[] = [],
): { data: T | null; error: string | null } {
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<string | null>(null);
  const fnRef = useRef(fn);
  fnRef.current = fn;

  useEffect(() => {
    if (!enabled) return;
    let cancelled = false;
    let timer: number | undefined;

    const tick = async () => {
      try {
        const result = await fnRef.current();
        if (cancelled) return;
        setData(result);
        setError(null);
      } catch (e) {
        if (cancelled) return;
        setError(String(e));
      }
      if (!cancelled) timer = window.setTimeout(tick, intervalMs);
    };
    tick();

    return () => {
      cancelled = true;
      window.clearTimeout(timer);
    };
  }, [enabled, intervalMs, ...deps]);

  return { data, error };
}
