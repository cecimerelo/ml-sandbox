import type { ComponentType } from 'react';

import { DiscriminantPanel } from './DiscriminantPanel';
import { KnnPanel } from './KnnPanel';
import { LinearRegressionPanel } from './LinearRegressionPanel';
import { LogisticRegressionPanel } from './LogisticRegressionPanel';
import { NaiveBayesPanel } from './NaiveBayesPanel';

export interface ChartPanelProps {
  jobId: string;
  file: File;
  target: string;
}

/** `DiscriminantPanel` is one component shared by two methods — it needs to know
 * which one to call `/api/train/{jobId}/{method}/charts` with, unlike every other
 * panel, which is already bound to a single method. */
function LdaPanel(props: ChartPanelProps) {
  return <DiscriminantPanel {...props} method="lda" />;
}

function QdaPanel(props: ChartPanelProps) {
  return <DiscriminantPanel {...props} method="qda" />;
}

/**
 * Which trained methods have a chart panel implemented so far (#83, FR-4.2) — one entry
 * per sub-issue, the frontend twin of `mlsandbox.api.CHART_BUILDERS`. A method missing
 * here just has no "View charts" button yet, not a bug.
 */
export const CHART_PANELS: Record<string, ComponentType<ChartPanelProps>> = {
  linear_regression: LinearRegressionPanel,
  logistic_regression: LogisticRegressionPanel,
  lda: LdaPanel,
  qda: QdaPanel,
  knn: KnnPanel,
  naive_bayes: NaiveBayesPanel,
};
