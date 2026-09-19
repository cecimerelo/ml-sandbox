import Grid from '@mui/material/Grid';
import { useState } from 'react';

import { DistributionTable } from '../../eda/DistributionTable';
import { PlotPanel } from '../../eda/PlotPanel';
import { ChartFetchStatus } from './ChartFetchStatus';
import { DecisionBoundarySection } from './DecisionBoundarySection';
import { GoalSubtitle } from './GoalSubtitle';
import { TuningCurveChart, tuningRows } from './TuningCurveChart';
import type { KnnCharts } from './types';
import { useChartData } from './useChartData';

/**
 * KNN's fixed set (FR-4.2, #99): a decision boundary and its accuracy-vs-K curve. No
 * confusion matrix — FR-4.2 doesn't list one for this method.
 */
export function KnnPanel({
  jobId,
  file,
  target,
}: {
  jobId: string;
  file: File;
  target: string;
}) {
  const [override, setOverride] = useState<{ x: string; y: string } | null>(null);

  const { data, failed } = useChartData<KnnCharts>(
    jobId,
    'knn',
    file,
    target,
    override ? { feature_x: override.x, feature_y: override.y } : undefined,
  );

  if (failed || !data) {
    return <ChartFetchStatus failed={failed} loaded={data !== null} />;
  }

  return (
    <Grid container spacing={2}>
      <Grid item xs={12} sm={6}>
        <DecisionBoundarySection
          idPrefix="knn"
          boundary={data.boundary}
          onSwap={(x, y) => setOverride({ x, y })}
        />
      </Grid>

      <Grid item xs={12} sm={6}>
        <PlotPanel
          title="Accuracy vs. K"
          subtitle={
            <GoalSubtitle
              description="How well the method scored, tried at every K it considered while tuning."
              goal={`A clear peak, with the chosen K sitting on or near it — K = ${data.tuning.chosen_k} was chosen here.`}
            />
          }
          chart={
            <TuningCurveChart
              points={data.tuning.points.map((p) => ({ x: p.k, score: p.score }))}
              chosenX={data.tuning.chosen_k}
              xLabel="K"
              formatX={(k) => `K = ${k}`}
            />
          }
          table={
            <DistributionTable
              rows={tuningRows(data.tuning.points.map((p) => ({ x: p.k, score: p.score })))}
              columnLabel="K"
              valueLabel="Score"
            />
          }
        />
      </Grid>
    </Grid>
  );
}
