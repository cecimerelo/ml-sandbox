/**
 * What the server reports about an uploaded file, once a target is chosen.
 *
 * Exact counts *and* the bands they map to. They answer different questions: the counts
 * let a user check the reading against their own file, the bands are what the engine
 * consumes. Showing only the bands would ask someone to do the banding themselves to
 * verify it.
 *
 * `regime` is deliberately absent — derived from the row and feature bands (D-028), so the
 * server computes it when the recommendation is asked for. A second copy here is how two
 * paths come to disagree about a derived value.
 */

import type {
  ClassBalance,
  FeatureBand,
  FeatureTypes,
  MissingLevel,
  RowBand,
  Task,
} from '../api/types';

export interface Detection {
  task: Task;
  rows: RowBand;
  features: FeatureBand;
  feature_types: FeatureTypes;
  missing: MissingLevel;
  class_balance: ClassBalance;

  n_rows: number;
  n_features: number;
  n_classes: number | null;
  missing_rate: number;
  /** Rows discarded because the outcome itself was blank. */
  dropped_rows: number;

  /**
   * Fields the file does not settle, by name.
   *
   * Per field, never global (FR-8.2). "Some of this might be wrong" tells a reader to
   * re-check everything, which they will not do; naming the field turns a warning into a
   * task with an end.
   */
  uncertain: string[];
}

/** Read-only in the form: facts about the file, not opinions someone can hold. */
export const READ_ONLY = ['rows', 'features'] as const;
