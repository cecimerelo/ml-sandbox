import type { ComponentType } from 'react';

import { BasisPanel } from './BasisPanel';
import { DecisionTreePanel } from './DecisionTreePanel';
import { DiscriminantPanel } from './DiscriminantPanel';
import { KnnPanel } from './KnnPanel';
import { LinearRegressionPanel } from './LinearRegressionPanel';
import { LogisticRegressionPanel } from './LogisticRegressionPanel';
import { NaiveBayesPanel } from './NaiveBayesPanel';
import { PcrPlsPanel } from './PcrPlsPanel';
import { RidgeLassoPanel } from './RidgeLassoPanel';

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

/** `RidgeLassoPanel` is likewise shared by two methods (#100). */
function RidgePanel(props: ChartPanelProps) {
  return <RidgeLassoPanel {...props} method="ridge" />;
}

function LassoPanel(props: ChartPanelProps) {
  return <RidgeLassoPanel {...props} method="lasso" />;
}

/** `PcrPlsPanel` is likewise shared by two methods (#101). */
function PcrPanel(props: ChartPanelProps) {
  return <PcrPlsPanel {...props} method="pcr" />;
}

function PlsPanel(props: ChartPanelProps) {
  return <PcrPlsPanel {...props} method="pls" />;
}

/** `BasisPanel` is shared by three methods (#102). */
function PolynomialPanel(props: ChartPanelProps) {
  return <BasisPanel {...props} method="polynomial" />;
}

function PolynomialInteractionsPanel(props: ChartPanelProps) {
  return <BasisPanel {...props} method="polynomial_interactions" />;
}

function SplinesPanel(props: ChartPanelProps) {
  return <BasisPanel {...props} method="splines" />;
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
  ridge: RidgePanel,
  lasso: LassoPanel,
  pcr: PcrPanel,
  pls: PlsPanel,
  polynomial: PolynomialPanel,
  polynomial_interactions: PolynomialInteractionsPanel,
  splines: SplinesPanel,
  decision_tree: DecisionTreePanel,
};
