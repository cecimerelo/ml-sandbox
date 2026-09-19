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
