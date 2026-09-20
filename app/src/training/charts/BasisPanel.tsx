import Grid from '@mui/material/Grid';

import { DistributionTable } from '../../eda/DistributionTable';
import { PlotPanel } from '../../eda/PlotPanel';
import { ChartFetchStatus } from './ChartFetchStatus';
import { FittedCurveChart } from './FittedCurveChart';
import { GoalSubtitle } from './GoalSubtitle';
import { ScatterChart, scatterSummaryRows } from './ScatterChart';
import type { BasisCharts } from './types';
import { useChartData } from './useChartData';

/**
 * Polynomial, Polynomial-with-Interactions, and Splines' fixed set (FR-4.2, #102):
 * a fitted curve and a residual plot. One panel covers all three — `polynomial_
 * interactions` has no row of its own in FR-4.2, mechanically the same kind of
 * model as `polynomial`.
 */
export function BasisPanel({
  jobId,
  file,
  target,
  method,
}: {
  jobId: string;
  file: File;
  target: string;
  method: 'polynomial' | 'polynomial_interactions' | 'splines';
}) {
  const { data, failed } = useChartData<BasisCharts>(jobId, method, file, target);

  if (failed || !data) {
    return <ChartFetchStatus failed={failed} loaded={data !== null} />;
  }

  return (
    <Grid container spacing={2}>
      <Grid item xs={12} sm={6}>
        <PlotPanel
          title="Fitted curve"
          subtitle={
            <GoalSubtitle
              description={`The model's own prediction as ${data.fitted_curve.feature} varies, every other column held at a typical value. Grey dots are the real rows.`}
              goal="The curve should track the real rows' overall shape, not swing wildly between them."
            />
          }
          chart={
            <FittedCurveChart
              feature={data.fitted_curve.feature}
              curve={data.fitted_curve.curve}
              actual={data.fitted_curve.actual}
            />
          }
          table={
            <DistributionTable
              rows={scatterSummaryRows(data.fitted_curve.actual, (p) => p.y)}
              columnLabel="Actual"
              valueLabel="Value"
            />
          }
        />
      </Grid>

      <Grid item xs={12} sm={6}>
        <PlotPanel
          title="Residual plot"
          subtitle={
            <GoalSubtitle
              description="Each point is one row: how far off the prediction was, against the prediction itself."
              goal="Scattered evenly around the dashed line is what a good fit looks like."
            />
          }
          chart={
            <ScatterChart
              points={data.residual.points}
              reference="zero"
              xLabel="Predicted"
              yLabel="Residual"
              ariaLabel="Residual plot: predicted value against actual minus predicted."
              pointLabel={(p) => `Predicted ${p.x.toFixed(1)}, residual ${p.y.toFixed(1)}`}
            />
          }
          table={
            <DistributionTable
              rows={scatterSummaryRows(data.residual.points, (p) => p.y)}
              columnLabel="Residual"
              valueLabel="Value"
            />
          }
        />
      </Grid>
    </Grid>
  );
}
