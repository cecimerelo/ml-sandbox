import Box from '@mui/material/Box';
import CircularProgress from '@mui/material/CircularProgress';
import Grid from '@mui/material/Grid';
import Typography from '@mui/material/Typography';
import { useEffect, useState } from 'react';

import { DistributionTable } from '../../eda/DistributionTable';
import { PlotPanel } from '../../eda/PlotPanel';
import { CoefficientChart, coefficientRows } from './CoefficientChart';
import { ScatterChart, scatterSummaryRows } from './ScatterChart';
import type { LinearRegressionCharts } from './types';

/** The "what am I looking at" line, plus a bold "what good looks like" line on its own
 * row underneath — the goal a reader should check the chart against. */
function GoalSubtitle({ description, goal }: { description: string; goal: React.ReactNode }) {
  return (
    <>
      {description}
      <br />
      <strong>👀 Goal: {goal}</strong>
    </>
  );
}

/**
 * The Linear Regression method's fixed chart set (FR-4.2, #95): residual plot,
 * predicted-vs-actual scatter, coefficient plot, leverage/Cook's-distance plot.
 *
 * Fetches once per (job, method, file) — the file is the same in-memory `File` object
 * the training panel already holds, re-sent here exactly as `EdaBlock` re-sends it for
 * every dataset-touching endpoint (FR-7.2): the backend never retains it between calls.
 */
export function LinearRegressionPanel({
  jobId,
  file,
  target,
}: {
  jobId: string;
  file: File;
  target: string;
}) {
  const [data, setData] = useState<LinearRegressionCharts | null>(null);
  const [failed, setFailed] = useState(false);

  useEffect(() => {
    let cancelled = false;
    setData(null);
    setFailed(false);
    async function load() {
      const body = new FormData();
      body.append('file', file);
      body.append('target', target);
      try {
        const response = await fetch(`/api/train/${jobId}/linear_regression/charts`, {
          method: 'POST',
          body,
        });
        if (cancelled) return;
        if (!response.ok) {
          setFailed(true);
          return;
        }
        setData(await response.json());
      } catch {
        if (!cancelled) setFailed(true);
      }
    }
    void load();
    return () => {
      cancelled = true;
    };
  }, [jobId, file, target]);

  if (failed) {
    return (
      <Typography color="text.secondary">
        We couldn't compute these charts. Try again — training itself already finished, so this
        is only the chart step.
      </Typography>
    );
  }

  if (!data) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
        <CircularProgress size={24} aria-label="Computing charts" />
      </Box>
    );
  }

  return (
    <Grid container spacing={2}>
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

      <Grid item xs={12} sm={6}>
        <PlotPanel
          title="Predicted vs. actual"
          subtitle={
            <GoalSubtitle
              description="Each point is one row: the actual value against what the model predicted for it."
              goal={`Points sitting on the dashed diagonal are exact matches — the closer, the better. R² = ${data.predicted_vs_actual.r2.toFixed(3)} here.`}
            />
          }
          chart={
            <ScatterChart
              points={data.predicted_vs_actual.points}
              reference="diagonal"
              xLabel="Actual"
              yLabel="Predicted"
              ariaLabel="Predicted vs. actual scatter, with a diagonal reference line for an exact match."
              pointLabel={(p) => `Actual ${p.x.toFixed(1)}, predicted ${p.y.toFixed(1)}`}
            />
          }
          table={
            <DistributionTable
              rows={scatterSummaryRows(data.predicted_vs_actual.points, (p) => p.y)}
              columnLabel="Predicted"
              valueLabel="Value"
            />
          }
        />
      </Grid>

      <Grid item xs={12} sm={6}>
        <PlotPanel
          title="Coefficients"
          subtitle={
            <GoalSubtitle
              description="How much each column moves the prediction, largest first. Blue pushes the prediction up, red pushes it down."
              goal="Each bar's size and direction should make sense for what its column represents — nothing surprisingly large from a column that shouldn't matter."
            />
          }
          chart={<CoefficientChart bars={data.coefficients.bars} />}
          table={<DistributionTable rows={coefficientRows(data.coefficients.bars)} columnLabel="Feature" valueLabel="Coefficient" />}
        />
      </Grid>

      <Grid item xs={12} sm={6}>
        <PlotPanel
          title="Leverage"
          subtitle={
            <GoalSubtitle
              description="Each point is one row: how much it alone pulls the fit (leverage) against how surprising its outcome was once that pull is accounted for (studentized residual)."
              goal="A cluster near the bottom-left — low pull, low surprise. Points far to the right or far from zero are worth a second look."
            />
          }
          chart={
            <ScatterChart
              points={data.leverage.points.map((p) => ({ x: p.leverage, y: p.studentized_residual }))}
              reference="zero"
              xLabel="Leverage"
              yLabel="Studentized residual"
              ariaLabel="Leverage against studentized residual, one point per row."
              pointLabel={(p) => `Leverage ${p.x.toFixed(3)}, studentized residual ${p.y.toFixed(2)}`}
            />
          }
          table={
            <DistributionTable
              rows={scatterSummaryRows(
                data.leverage.points.map((p) => ({ x: p.leverage, y: p.studentized_residual })),
                (p) => p.x
              )}
              columnLabel="Leverage"
              valueLabel="Value"
            />
          }
        />
      </Grid>
    </Grid>
  );
}
