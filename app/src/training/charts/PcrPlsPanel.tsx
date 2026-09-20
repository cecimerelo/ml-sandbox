import Grid from '@mui/material/Grid';

import { DistributionTable } from '../../eda/DistributionTable';
import { PlotPanel } from '../../eda/PlotPanel';
import { ChartFetchStatus } from './ChartFetchStatus';
import { GoalSubtitle } from './GoalSubtitle';
import { TuningCurveChart, tuningRows } from './TuningCurveChart';
import type { PcrPlsCharts } from './types';
import { useChartData } from './useChartData';
import { VarianceExplainedChart, varianceExplainedRows } from './VarianceExplainedChart';

/**
 * PCR and PLS's fixed set (FR-4.2, #101): variance explained vs. components, and CV
 * score vs. components — "the pair that actually picks how many components to
 * keep." PCR's variance-explained chart is predictors-only (PCA never sees the
 * target); PLS's shows both, since its components are built to explain the target.
 */
export function PcrPlsPanel({
  jobId,
  file,
  target,
  method,
}: {
  jobId: string;
  file: File;
  target: string;
  method: 'pcr' | 'pls';
}) {
  const { data, failed } = useChartData<PcrPlsCharts>(jobId, method, file, target);

  if (failed || !data) {
    return <ChartFetchStatus failed={failed} loaded={data !== null} />;
  }

  const hasYVariance = data.variance_explained.points.some((p) => p.y_variance !== null);

  return (
    <Grid container spacing={2}>
      <Grid item xs={12} sm={6}>
        <PlotPanel
          title="Variance explained"
          subtitle={
            <GoalSubtitle
              description={
                hasYVariance
                  ? 'How much of the predictors\' and the target\'s variance the first N components capture, cumulatively.'
                  : 'How much of the predictors\' variance the first N components capture, cumulatively.'
              }
              goal={`Diminishing returns past the chosen count — components after ${data.variance_explained.chosen_x} adding little more.`}
            />
          }
          chart={
            <VarianceExplainedChart
              points={data.variance_explained.points}
              chosenX={data.variance_explained.chosen_x}
              xLabel={data.variance_explained.x_label}
            />
          }
          table={
            <DistributionTable
              rows={varianceExplainedRows(data.variance_explained.points)}
              columnLabel="Components"
              valueLabel="Predictor variance"
            />
          }
        />
      </Grid>

      <Grid item xs={12} sm={6}>
        <PlotPanel
          title="Tuning curve"
          subtitle={
            <GoalSubtitle
              description="How well the method scored, tried at every component count it considered while tuning."
              goal={`A clear peak, with the chosen count sitting on or near it — ${data.tuning.x_label} = ${data.tuning.chosen_x} was chosen here.`}
            />
          }
          chart={
            <TuningCurveChart
              points={data.tuning.points.map((p) => ({ x: p.x, score: p.score }))}
              chosenX={data.tuning.chosen_x}
              xLabel={data.tuning.x_label}
              formatX={(x) => `${data.tuning.x_label} = ${x}`}
            />
          }
          table={
            <DistributionTable
              rows={tuningRows(data.tuning.points.map((p) => ({ x: p.x, score: p.score })))}
              columnLabel={data.tuning.x_label}
              valueLabel="Score"
            />
          }
        />
      </Grid>
    </Grid>
  );
}
