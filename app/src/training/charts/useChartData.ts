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
): { data: T | null; failed: boolean } {
  const [data, setData] = useState<T | null>(null);
  const [failed, setFailed] = useState(false);

  useEffect(() => {
    let cancelled = false;
    setData(null);
    setFailed(false);
    async function load() {
      const body = new FormData();
      body.append('file', file);
      body.append('target', target);
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
  }, [jobId, method, file, target]);

  return { data, failed };
}
