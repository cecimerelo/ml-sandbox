import Grid from '@mui/material/Grid';
import Typography from '@mui/material/Typography';

import { DistributionTable } from '../../eda/DistributionTable';
import { PlotPanel } from '../../eda/PlotPanel';
import { ChartFetchStatus } from './ChartFetchStatus';
import { GoalSubtitle } from './GoalSubtitle';
import { ShrinkagePathChart, shrinkageRows } from './ShrinkagePathChart';
import { TuningCurveChart, tuningRows } from './TuningCurveChart';
import type { ShrinkageCharts } from './types';
import { useChartData } from './useChartData';

/**
 * Ridge and Lasso's fixed set (FR-4.2, #100), shared by both their regression and
 * classification builds: a coefficient shrinkage path and a CV-error/score-vs-
 * regularization tuning curve. The path is empty for a multiclass classification
 * target — `coef_` there has one row per class, the same reason Logistic Regression's
 * own coefficient plot is empty for a multiclass target.
 */
export function RidgeLassoPanel({
  jobId,
  file,
  target,
  method,
}: {
  jobId: string;
  file: File;
  target: string;
  method: 'ridge' | 'lasso';
}) {
  const { data, failed } = useChartData<ShrinkageCharts>(jobId, method, file, target);

  if (failed || !data) {
    return <ChartFetchStatus failed={failed} loaded={data !== null} />;
  }

  const hasShrinkagePath = data.shrinkage.points.length > 0;

  return (
    <Grid container spacing={2}>
      <Grid item xs={12} sm={6}>
        {hasShrinkagePath ? (
          <PlotPanel
            title="Coefficient shrinkage path"
            subtitle={
              <GoalSubtitle
                description={`Every column's coefficient as the regularization strength (${data.shrinkage.x_label}) varies. The 3 largest at the chosen strength are labelled; everything else is shown faint for context.`}
                goal="The labelled paths should settle near the chosen strength, not still swinging wildly."
              />
            }
            chart={
              <ShrinkagePathChart
                points={data.shrinkage.points}
                promotedFeatures={data.shrinkage.promoted_features}
                xLabel={data.shrinkage.x_label}
              />
            }
            table={
              <DistributionTable
                rows={shrinkageRows(data.shrinkage.points)}
                columnLabel="Feature"
                valueLabel="Coefficient"
              />
            }
          />
        ) : (
          <Typography color="text.secondary">
            The shrinkage path only applies to a two-outcome target — this one has more than two,
            so there's nothing to plot here.
          </Typography>
        )}
      </Grid>

      <Grid item xs={12} sm={6}>
        <PlotPanel
          title="Tuning curve"
          subtitle={
            <GoalSubtitle
              description={`How well the method scored, tried at every regularization strength (${data.tuning.x_label}) it considered while tuning.`}
              goal={`A clear peak, with the chosen strength sitting on or near it — ${data.tuning.x_label} = ${data.tuning.chosen_x.toPrecision(3)} was chosen here.`}
            />
          }
          chart={
            <TuningCurveChart
              points={data.tuning.points.map((p) => ({ x: p.x, score: p.score }))}
              chosenX={data.tuning.chosen_x}
              xLabel={data.tuning.x_label}
              formatX={(x) => `${data.tuning.x_label} = ${x.toPrecision(3)}`}
              xScale="log"
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
