/**
 * What `/api/recommend` answers with.
 *
 * Mirrors the pydantic models in `mlsandbox.recommend`. Checked against the running server
 * by the endpoint's own tests rather than restated here as truth — this file is the
 * browser's half of a contract, not its definition.
 */

export interface Position {
  /** Where the method sits, e.g. "flexible" or "readable". */
  label: string;
  /** What that means for this method, in one sentence. */
  detail: string;
}

export interface Axis {
  /** e.g. "high", "moderate", "opaque". */
  word: string;
  /** 1 (worst/lowest) to 3 (best/highest), never coloured — an ordinal rating, not a
   * red/amber/green judgement. */
  step: 1 | 2 | 3;
}

export interface Characteristics {
  method: string;
  label: string;
  interpretability: Axis;
  handles_non_linearity: Axis;
  handles_missing_values: Axis;
  /**
   * Computed from the benchmark, not declared from theory (D-049): nothing in the method
   * registry states an expected accuracy, and asserting one by hand risked contradicting
   * a measurement the study actually made.
   */
  accuracy_potential: Axis;
  /** Also computed from the benchmark, for the same reason. */
  training_speed: Axis;
}

export interface DecisionFactor {
  /** The form question whose answer fired this, in the words that question uses. */
  question: string;
  /** What the user said. */
  answer: string;
  /** What that answer argues, in the words shown to the user. */
  claim: string;
  /** The best-ranked method this same answer pushed down, if any. */
  over: string | null;
}

export interface Suggestion {
  method: string;
  label: string;
  flexibility: Position;
  interpretability: Position;
  /** Predicted distance below the best available method. Zero means "expected to be best". */
  expected_shortfall: number;
  /** Spread across the model's trees. Where intervals overlap, the ordering is not evidence. */
  uncertainty: number;
  /** The claims that fired, in the words shown to the user. */
  reasons: string[];
  /**
   * The same claims as `reasons`, each tied to the answer that fired it and the method it
   * beat. What the flowchart is built from: it is literally the path the engine took, not
   * a diagram redrawn from it.
   */
  factors: DecisionFactor[];
  /** This method's row in the comparison table, or `null` if the benchmark has no row for
   * it — a fact worth being able to see, not a reason to hide the rest of the panel. */
  characteristics: Characteristics | null;
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
