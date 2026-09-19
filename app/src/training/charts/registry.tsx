import type { ComponentType } from 'react';

import { LinearRegressionPanel } from './LinearRegressionPanel';
import { LogisticRegressionPanel } from './LogisticRegressionPanel';

export interface ChartPanelProps {
  jobId: string;
  file: File;
  target: string;
}

/**
 * Which trained methods have a chart panel implemented so far (#83, FR-4.2) — one entry
 * per sub-issue, the frontend twin of `mlsandbox.api.CHART_BUILDERS`. A method missing
 * here just has no "View charts" button yet, not a bug.
 */
export const CHART_PANELS: Record<string, ComponentType<ChartPanelProps>> = {
  linear_regression: LinearRegressionPanel,
  logistic_regression: LogisticRegressionPanel,
};
