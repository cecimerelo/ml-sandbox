import Box from '@mui/material/Box';
import FormControl from '@mui/material/FormControl';
import InputLabel from '@mui/material/InputLabel';
import MenuItem from '@mui/material/MenuItem';
import Select from '@mui/material/Select';
import Typography from '@mui/material/Typography';

import { PlotPanel } from '../../eda/PlotPanel';
import { spacing } from '../../theme/tokens';
import { boundarySummary, DecisionBoundaryChart } from './DecisionBoundaryChart';
import { GoalSubtitle } from './GoalSubtitle';
import type { DecisionBoundary } from './types';

/**
 * The "Decision boundary" `PlotPanel` plus FR-4.3's axis-swap controls — shared by
 * every method with a boundary in its fixed set (LDA/QDA, #97; KNN, #99). `idPrefix`
 * keeps each panel's `Select` label ids unique when more than one is on the page at
 * once (e.g. two chart panels open together).
 */
export function DecisionBoundarySection({
  idPrefix,
  boundary,
  onSwap,
}: {
  idPrefix: string;
  boundary: DecisionBoundary;
  onSwap: (featureX: string, featureY: string) => void;
}) {
  const canSwap = boundary.numeric_features.length >= 2;

  return (
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
              <InputLabel id={`${idPrefix}-feature-x`}>Horizontal axis</InputLabel>
              <Select
                labelId={`${idPrefix}-feature-x`}
                label="Horizontal axis"
                value={boundary.feature_x}
                onChange={(event) => onSwap(event.target.value, boundary.feature_y)}
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
              <InputLabel id={`${idPrefix}-feature-y`}>Vertical axis</InputLabel>
              <Select
                labelId={`${idPrefix}-feature-y`}
                label="Vertical axis"
                value={boundary.feature_y}
                onChange={(event) => onSwap(boundary.feature_x, event.target.value)}
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
  );
}
