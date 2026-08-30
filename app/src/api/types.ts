/**
 * The contract between the form and the engine.
 *
 * These unions mirror the Python `Literal` types in `mlsandbox.metafeatures` and
 * `mlsandbox.layer1` exactly. They are the same bands the study trained on, which is what
 * D-027's train/serve agreement rests on — an answer the model never saw must be
 * impossible to express here, not merely rejected at the far end.
 *
 * Kept in step by `types.test.ts`, which reads the exported `config/metafeatures.json`
 * rather than trusting this file. Two hand-maintained copies of the same vocabulary drift,
 * and when they do the model does not error: it predicts.
 */

export type Task = 'regression' | 'binary classification' | 'multiclass classification';
export type RowBand = '<500' | '500-10k' | '>10k';
export type FeatureBand = '<10' | '10-50' | '>50';
export type FeatureTypes = 'numeric' | 'categorical' | 'mixed';
export type MissingLevel = 'none' | 'some' | 'a lot';
export type ClassBalance = 'roughly equal' | 'one class dominates' | 'not applicable';

export type Explainability = 'not important' | 'somewhat' | 'critical';
export type Suspicion = 'no' | 'unsure' | 'yes';

/**
 * What the form sends. Note `regime` is absent: it is derived from the two bands rather
 * than asked, because asking a user to estimate observations per predictor is asking them
 * to do the arithmetic they came here to avoid (D-028). The server derives it, so there is
 * one definition of it rather than two.
 */
export interface RecommendationRequest {
  task: Task;
  rows: RowBand;
  features: FeatureBand;
  feature_types: FeatureTypes;
  missing: MissingLevel;
  class_balance: ClassBalance;
  explainability: Explainability;
  suspects_non_linearity: Suspicion;
  suspects_interactions: Suspicion;
}

export interface MethodRecommendation {
  method: string;
  label: string;
  /** Where it sits against the best available option. Smaller is better; zero is best. */
  expected_shortfall: number;
  /**
   * Spread across the model's trees. Where two methods' intervals overlap, the ordering
   * between them is not evidence, and the panel has to say so rather than present a
   * ranking that looks decisive.
   */
  uncertainty: number;
  /** The claims that fired, in the words shown to the user. Never reconstructed later. */
  reasons: string[];
}

export interface RecommendationResponse {
  recommended: MethodRecommendation;
  alternatives: MethodRecommendation[];
  /**
   * Methods a stated constraint removed, with what it cost. Returned rather than hidden:
   * withholding the best method silently leaves the user unable to weigh the trade (D-035).
   */
  excluded: MethodRecommendation[];
}
