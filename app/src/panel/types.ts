/**
 * What `/api/recommend` answers with.
 *
 * Mirrors the pydantic models in `mlsandbox.recommend`. Checked against the running server
 * by the endpoint's own tests rather than restated here as truth — this file is the
 * browser's half of a contract, not its definition.
 */

export interface Suggestion {
  method: string;
  label: string;
  /** Predicted distance below the best available method. Zero means "expected to be best". */
  expected_shortfall: number;
  /** Spread across the model's trees. Where intervals overlap, the ordering is not evidence. */
  uncertainty: number;
  /** The claims that fired, in the words shown to the user. */
  reasons: string[];
  excluded_by_constraint: boolean;
}

export interface Support {
  field: string;
  answer: string;
  datasets: number;
  total: number;
}

export interface Recommendation {
  recommended: Suggestion;
  alternatives: Suggestion[];
  excluded: Suggestion[];
  support: Support;
  provisional: boolean;
}

/**
 * The engine's 0–1 fit score, from the shortfall it predicts.
 *
 * `1 − shortfall`, and **not rescaled across the methods on screen.** Rescaling is the
 * tempting version: make the best method fill the bar and the worst fall short, and the
 * panel looks decisive. It would also manufacture separation the data does not have.
 *
 * The study's own headline is that these methods sit close together — a fixed choice ties
 * a trained model, and most datasets have several methods within one standard deviation of
 * the best (F-003, D-036). Bars that all look similar are the honest picture. An interface
 * that stretched them would be contradicting the thesis it is built on.
 */
export function fitScore(shortfall: number): number {
  return Math.min(1, Math.max(0, 1 - shortfall));
}

/**
 * Whether two methods are far enough apart for the ordering between them to mean anything.
 *
 * Layer 2 reports the spread across its trees, and where the intervals overlap the
 * ordering is a coin toss the panel must not present as a finding — the model is trained
 * on around a hundred datasets, and a confident wrong answer is worse than a hesitant one.
 */
export function indistinguishable(a: Suggestion, b: Suggestion): boolean {
  return Math.abs(a.expected_shortfall - b.expected_shortfall) <= a.uncertainty + b.uncertainty;
}
