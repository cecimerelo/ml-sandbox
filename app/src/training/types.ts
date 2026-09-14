/**
 * Mirrors `mlsandbox.training_jobs`/`api.py`'s training endpoints exactly — see
 * `MethodStatusOut`/`TrainingStatus` in `src/mlsandbox/api.py`.
 */

export type MethodStatus = 'pending' | 'running' | 'ok' | 'timeout' | 'error' | 'stopped';

export interface MethodResult {
  method: string;
  status: MethodStatus;
  mean_score: number | null;
  std_score: number | null;
  fold_scores: number[];
  fit_seconds: number | null;
  detail: string | null;
}

export interface TrainingStatus {
  id: string;
  methods: string[];
  /** The per-method timeout tier (FR-8.4), fixed for the whole job — what the loading
   * estimate multiplies the remaining method count by. */
  budget_seconds: number;
  current: string | null;
  halted_early: boolean;
  aborted: boolean;
  abort_detail: string | null;
  done: boolean;
  results: Record<string, MethodResult>;
}
