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
