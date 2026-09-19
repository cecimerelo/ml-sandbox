import { useEffect, useState } from 'react';

/**
 * Fetches one method's chart data from `POST /api/train/{jobId}/{method}/charts`,
 * re-sending `file` exactly as `EdaBlock` re-sends it for every dataset-touching
 * endpoint (FR-7.2) — the backend never retains it between calls, and the pipeline
 * this reads from is the one `/api/train` already fit, never refit here.
 */
export function useChartData<T>(
  jobId: string,
  method: string,
  file: File,
  target: string,
  /** Method-specific overrides beyond file/target — FR-4.3's "swap the selected
   * features" (`feature_x`/`feature_y`) is the first of these. Absent for every method
   * with nothing to override. */
  extraParams?: Record<string, string>,
): { data: T | null; failed: boolean } {
  const [data, setData] = useState<T | null>(null);
  const [failed, setFailed] = useState(false);
  // Compared by value below, not by the object reference `extraParams` gets on every
  // render — a plain object literal passed inline at the call site would otherwise
  // refetch on every render even when nothing in it actually changed.
  const extraParamsKey = extraParams ? JSON.stringify(extraParams) : '';

  useEffect(() => {
    let cancelled = false;
    setData(null);
    setFailed(false);
    async function load() {
      const body = new FormData();
      body.append('file', file);
      body.append('target', target);
      for (const [key, value] of Object.entries(extraParams ?? {})) {
        body.append(key, value);
      }
      try {
        const response = await fetch(`/api/train/${jobId}/${method}/charts`, {
          method: 'POST',
          body,
        });
        if (cancelled) return;
        if (!response.ok) {
          setFailed(true);
          return;
        }
        setData(await response.json());
      } catch {
        if (!cancelled) setFailed(true);
      }
    }
    void load();
    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps -- extraParamsKey stands in
    // for extraParams (see its own comment above); including both would defeat the point.
  }, [jobId, method, file, target, extraParamsKey]);

  return { data, failed };
}
