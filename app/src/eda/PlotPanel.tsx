import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Paper from '@mui/material/Paper';
import Typography from '@mui/material/Typography';
import { useState } from 'react';
import type React from 'react';

import { chart, spacing } from '../theme/tokens';

/**
 * `{components.plot-panel}` — the atomic unit every chart in the product renders inside.
 *
 * Anatomy, top to bottom, per DESIGN.md: title (always) → subtitle (optional — the home
 * of every truncation disclosure) → the plot at its aspect box → legend → caption. A
 * `View as table` button sits top-right and toggles the box between `chart` and `table`,
 * **inside the same box** so the panel's outer height never changes and the grid above
 * it never reflows.
 *
 * **Structural rule, not a style choice:** `chart` is the only thing inside the plot box
 * that may be an SVG carrying `role="img"`. Everything else in this component — title,
 * subtitle, legend, caption, the toggle — is an ordinary DOM sibling outside it, or the
 * text-equivalent fallback these carry becomes unreachable by the people it exists for.
 */
export function PlotPanel({
  title,
  subtitle,
  chart: chartNode,
  table,
  legend,
  caption,
  aspect = spacing.plotAspect,
}: {
  title: string;
  /** The beginner-facing "what am I looking at" line. Also where a truncation — top 15
   * categories, 20 of 500 features shown — is stated, never left silent. */
  subtitle?: string;
  /** The graphic element. The only child here allowed to carry `role="img"`. */
  chart: React.ReactNode;
  /** The same data as `chart`, in the table form DESIGN.md specifies for this family. */
  table: React.ReactNode;
  legend?: React.ReactNode;
  caption?: string;
  aspect?: string;
}) {
  const [showTable, setShowTable] = useState(false);

  return (
    <Paper
      variant="outlined"
      sx={{
        p: { xs: `${spacing.plotPanelPaddingCompact}px`, sm: `${spacing.plotPanelPadding}px` },
        borderRadius: 1,
        borderColor: chart.gridline.hex,
      }}
    >
      <Box sx={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between' }}>
        <Box>
          <Typography sx={{ fontWeight: 700 }}>{title}</Typography>
          {subtitle && (
            <Typography variant="body2" color="text.secondary" sx={{ mt: 0.25 }}>
              {subtitle}
            </Typography>
          )}
        </Box>
        <Button size="small" onClick={() => setShowTable((v) => !v)} sx={{ flexShrink: 0 }}>
          {showTable ? 'View as chart' : 'View as table'}
        </Button>
      </Box>

      {/* The same aspect box either way, so toggling never reflows the grid above it. */}
      <Box
        sx={{
          mt: 2,
          aspectRatio: aspect,
          overflow: showTable ? 'auto' : 'visible',
          border: showTable ? `1px solid ${chart.gridline.hex}` : 'none',
          borderRadius: showTable ? 1 : 0,
        }}
      >
        {showTable ? table : chartNode}
      </Box>

      {!showTable && legend && <Box sx={{ mt: 1.5 }}>{legend}</Box>}

      {caption && (
        <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
          {caption}
        </Typography>
      )}
    </Paper>
  );
}
