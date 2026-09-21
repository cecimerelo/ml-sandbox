/**
 * The chart endpoint's contract with `mlsandbox.charts` and `mlsandbox.api` (#83, FR-4.2).
 *
 * One file per method eventually — `LinearRegressionCharts` is the first (#95); #96-#107
 * add their own shapes here as each sub-issue lands.
 */

export interface ScatterPoint {
  x: number;
  y: number;
}

export interface ResidualPlot {
  points: ScatterPoint[];
}

export interface PredictedVsActual {
  points: ScatterPoint[];
  r2: number;
}

export interface CoefficientBar {
  feature: string;
  value: number;
}

export interface CoefficientPlot {
  /** Every coefficient, sorted by |value| descending — the full list, DESIGN.md's
   * table form for this family. `CoefficientChart` slices its own top-20 for the plot. */
  bars: CoefficientBar[];
}

export interface LeveragePoint {
  leverage: number;
  studentized_residual: number;
}

export interface LeveragePlot {
  points: LeveragePoint[];
}

export interface LinearRegressionCharts {
  residual: ResidualPlot;
  predicted_vs_actual: PredictedVsActual;
  coefficients: CoefficientPlot;
  leverage: LeveragePlot;
}

export interface RocPoint {
  false_positive_rate: number;
  true_positive_rate: number;
}

export interface RocCurve {
  points: RocPoint[];
  auc: number;
  positive_class: string;
}

export interface ConfusionMatrix {
  labels: string[];
  /** `matrix[i][j]`: rows whose actual class was `labels[i]`, predicted as `labels[j]`. */
  matrix: number[][];
}

export interface LogisticRegressionCharts {
  /** `null` for a target with more than two classes — a binary-only chart, per
   * `mlsandbox.charts.logistic_regression_charts`. */
  roc: RocCurve | null;
  confusion_matrix: ConfusionMatrix;
  /** Empty for a multiclass target — `coef_` has one row per class there, not the
   * single signed value per feature this chart plots. */
  coefficients: CoefficientPlot;
}

export interface BoundaryCell {
  x: number;
  y: number;
  predicted_class: string;
}

export interface BoundaryPoint {
  x: number;
  y: number;
  actual_class: string;
}

export interface DecisionBoundary {
  feature_x: string;
  feature_y: string;
  /** Every numeric column — what a "swap the selected features" control (FR-4.3)
   * chooses between. Always includes `feature_x`/`feature_y` themselves. */
  numeric_features: string[];
  classes: string[];
  /** Empty when there aren't two numeric columns to plot, or when `classes.length`
   * exceeds the family's class cap — either way, `too_many_classes` and
   * `numeric_features` say which. */
  grid: BoundaryCell[];
  points: BoundaryPoint[];
  too_many_classes: boolean;
  /** `true` when classes outnumber half the rows — the signature of a continuous
   * column (price, an ID) trained as if it were categorical, not just a category
   * count too high to plot. */
  looks_continuous: boolean;
}

export interface DiscriminantCharts {
  boundary: DecisionBoundary;
  confusion_matrix: ConfusionMatrix;
}

export interface KnnTuningPoint {
  k: number;
  score: number;
}

export interface KnnTuningCurve {
  points: KnnTuningPoint[];
  chosen_k: number;
}

export interface KnnCharts {
  boundary: DecisionBoundary;
  tuning: KnnTuningCurve;
}

export interface NaiveBayesCharts {
  /** `null` for a target with more than two classes — a binary-only chart, per
   * `mlsandbox.charts.naive_bayes_charts`. */
  roc: RocCurve | null;
  confusion_matrix: ConfusionMatrix;
}

export interface RegularizationPoint {
  x: number;
  score: number;
}

export interface RegularizationCurve {
  points: RegularizationPoint[];
  chosen_x: number;
  /** The estimator's own parameter name — "α" for Ridge/Lasso, "C" for the
   * `LogisticRegressionCV` classification uses. */
  x_label: string;
}

export interface ShrinkagePoint {
  feature: string;
  x: number;
  coefficient: number;
}

export interface ShrinkagePath {
  points: ShrinkagePoint[];
  /** The top 3 by |coefficient| at the chosen regularization strength — empty for a
   * multiclass classification Ridge/Lasso, the same reason Logistic Regression's own
   * coefficient plot is empty for a multiclass target. */
  promoted_features: string[];
  x_label: string;
}

export interface ShrinkageCharts {
  shrinkage: ShrinkagePath;
  tuning: RegularizationCurve;
}

export interface ComponentPoint {
  x: number;
  x_variance: number;
  /** Cumulative variance explained in the target — `null` for PCR: PCA never sees
   * the target, so there is no such number. Present for PLS, whose components are
   * chosen specifically to explain it. */
  y_variance: number | null;
}

export interface VarianceExplainedCurve {
  points: ComponentPoint[];
  chosen_x: number;
  x_label: string;
}

export interface PcrPlsCharts {
  variance_explained: VarianceExplainedCurve;
  tuning: RegularizationCurve;
}

export interface FittedCurve {
  feature: string;
  /** The pipeline's own prediction as `feature` sweeps its observed range, every
   * other feature held at a representative value. */
  curve: ScatterPoint[];
  /** The real (feature, target) pairs, unmodified. */
  actual: ScatterPoint[];
}

export interface BasisCharts {
  fitted_curve: FittedCurve;
  residual: ResidualPlot;
}

export interface TreeNode {
  id: number;
  parent_id: number | null;
  depth: number;
  is_leaf: boolean;
  split_feature: string | null;
  split_threshold: number | null;
  n_samples: number;
  predicted_value: string;
  /** Set only on a synthetic truncation stub: how many real splits it collapses. */
  truncated_splits: number | null;
}

export interface DecisionTreeDiagram {
  nodes: TreeNode[];
  rendered_depth: number;
  total_depth: number;
}

export interface FeatureImportanceBar {
  feature: string;
  value: number;
}

export interface FeatureImportancePlot {
  bars: FeatureImportanceBar[];
}

export interface PruningPoint {
  n_leaves: number;
  score: number;
}

export interface PruningCurve {
  points: PruningPoint[];
  chosen_n_leaves: number;
  x_label: string;
}

export interface DecisionTreeCharts {
  tree: DecisionTreeDiagram;
  importance: FeatureImportancePlot;
  pruning: PruningCurve;
}
