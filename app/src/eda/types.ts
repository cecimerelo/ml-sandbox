/**
 * The EDA block's contract with `mlsandbox.eda` and `mlsandbox.api`.
 *
 * Every shape here is a reduction — bins, counts, category labels — never a row. That is
 * the backend's privacy claim, and the frontend's types exist to make it impossible for a
 * future field to smuggle one in unnoticed.
 */

export interface HistogramBin {
  start: number;
  end: number;
  count: number;
}

export interface Histogram {
  column: string;
  kind: 'numeric';
  bins: HistogramBin[];
  missing: number;
}

export interface CategoryCount {
  category: string;
  count: number;
}

export interface CategoricalBars {
  column: string;
  kind: 'categorical';
  categories: CategoryCount[];
  other_count: number;
  other_categories: number;
  missing: number;
}

export type Distribution = Histogram | CategoricalBars;

export interface ColumnKind {
  column: string;
  kind: 'numeric' | 'categorical';
}

export interface ColumnInventory {
  columns: ColumnKind[];
  total: number;
}

export interface DistributionsResult {
  target: Distribution;
  features: Distribution[];
}
