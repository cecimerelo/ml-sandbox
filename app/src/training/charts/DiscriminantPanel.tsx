import Box from '@mui/material/Box';
import FormControl from '@mui/material/FormControl';
import Grid from '@mui/material/Grid';
import InputLabel from '@mui/material/InputLabel';
import MenuItem from '@mui/material/MenuItem';
import Select from '@mui/material/Select';
import Typography from '@mui/material/Typography';
import { useState } from 'react';

import { PlotPanel } from '../../eda/PlotPanel';
import { spacing } from '../../theme/tokens';
import { ChartFetchStatus } from './ChartFetchStatus';
import { ConfusionMatrixChart, ConfusionMatrixTable } from './ConfusionMatrixChart';
import { boundarySummary, DecisionBoundaryChart } from './DecisionBoundaryChart';
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

  const { boundary } = data;
  const canSwap = boundary.numeric_features.length >= 2;

  return (
    <Grid container spacing={2}>
      <Grid item xs={12} sm={6}>
        <PlotPanel
          title="Decision boundary"
          subtitle={
            <GoalSubtitle
              description={`Each region is what the model predicts across ${boundary.feature_x} and ${boundary.feature_y}; each point is one real row, at its actual outcome.`}
              goal="Points should mostly sit inside the region matching their own shape and colour — that's the model getting them right."
            />
          }
          chart={<DecisionBoundaryChart boundary={boundary} />}
          table={<Typography color="text.secondary">{boundarySummary(boundary)}</Typography>}
          aspect={spacing.plotAspectSquare}
          legend={
            canSwap && (
              <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
                <FormControl size="small" sx={{ minWidth: 160 }}>
                  <InputLabel id={`${method}-feature-x`}>Horizontal axis</InputLabel>
                  <Select
                    labelId={`${method}-feature-x`}
                    label="Horizontal axis"
                    value={boundary.feature_x}
                    onChange={(event) =>
                      setOverride({ x: event.target.value, y: boundary.feature_y })
                    }
                  >
                    {/* Excludes whatever the vertical axis already plots — the same
                        column on both axes has no boundary to draw. */}
                    {boundary.numeric_features
                      .filter((feature) => feature !== boundary.feature_y)
                      .map((feature) => (
                        <MenuItem key={feature} value={feature}>
                          {feature}
                        </MenuItem>
                      ))}
                  </Select>
                </FormControl>
                <FormControl size="small" sx={{ minWidth: 160 }}>
                  <InputLabel id={`${method}-feature-y`}>Vertical axis</InputLabel>
                  <Select
                    labelId={`${method}-feature-y`}
                    label="Vertical axis"
                    value={boundary.feature_y}
                    onChange={(event) =>
                      setOverride({ x: boundary.feature_x, y: event.target.value })
                    }
                  >
                    {boundary.numeric_features
                      .filter((feature) => feature !== boundary.feature_x)
                      .map((feature) => (
                        <MenuItem key={feature} value={feature}>
                          {feature}
                        </MenuItem>
                      ))}
                  </Select>
                </FormControl>
              </Box>
            )
          }
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
