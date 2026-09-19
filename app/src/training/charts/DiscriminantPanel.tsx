import Grid from '@mui/material/Grid';
import { useState } from 'react';

import { PlotPanel } from '../../eda/PlotPanel';
import { spacing } from '../../theme/tokens';
import { ChartFetchStatus } from './ChartFetchStatus';
import { ConfusionMatrixChart, ConfusionMatrixTable } from './ConfusionMatrixChart';
import { DecisionBoundarySection } from './DecisionBoundarySection';
import { GoalSubtitle } from './GoalSubtitle';
import type { DiscriminantCharts } from './types';
import { useChartData } from './useChartData';

/**
 * LDA and QDA's fixed set (FR-4.2, #97): a decision boundary and a confusion matrix.
 * FR-4.3's "auto-selects the 2 most important features, the user can swap them" is the
 * pair of selects here — changing either re-fetches with that pair, replacing the
 * backend's own auto-selection.
 */
export function DiscriminantPanel({
  jobId,
  method,
  file,
  target,
}: {
  jobId: string;
  method: string;
  file: File;
  target: string;
}) {
  const [override, setOverride] = useState<{ x: string; y: string } | null>(null);

  const { data, failed } = useChartData<DiscriminantCharts>(
    jobId,
    method,
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
          idPrefix={method}
          boundary={data.boundary}
          onSwap={(x, y) => setOverride({ x, y })}
        />
      </Grid>

      <Grid item xs={12} sm={6}>
        <PlotPanel
          title="Confusion matrix"
          subtitle={
            <GoalSubtitle
              description="Each cell is how many rows with that actual outcome (row) the model predicted as that outcome (column)."
              goal="A heavy diagonal and light everywhere else — most rows landing where actual and predicted agree."
            />
          }
          chart={<ConfusionMatrixChart data={data.confusion_matrix} />}
          table={<ConfusionMatrixTable data={data.confusion_matrix} />}
          aspect={spacing.plotAspectSquare}
        />
      </Grid>
    </Grid>
  );
}
