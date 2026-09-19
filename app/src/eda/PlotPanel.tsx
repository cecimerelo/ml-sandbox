import OpenInFullIcon from '@mui/icons-material/OpenInFull';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Dialog from '@mui/material/Dialog';
import DialogContent from '@mui/material/DialogContent';
import DialogTitle from '@mui/material/DialogTitle';
import IconButton from '@mui/material/IconButton';
import Paper from '@mui/material/Paper';
import Tooltip from '@mui/material/Tooltip';
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
   * categories, 20 of 500 features shown — is stated, never left silent. A plain string
   * renders `\n` as a real line break (`white-space: pre-line`); pass a node instead
   * (e.g. wrapping a "what good looks like" line in `<strong>`) when part of it needs
   * its own emphasis. */
  subtitle?: React.ReactNode;
  /** The graphic element. The only child here allowed to carry `role="img"`. */
  chart: React.ReactNode;
  /** The same data as `chart`, in the table form DESIGN.md specifies for this family. */
  table: React.ReactNode;
  legend?: React.ReactNode;
  caption?: string;
  aspect?: string;
}) {
  const [showTable, setShowTable] = useState(false);
  const [expanded, setExpanded] = useState(false);

  const plotBox = (boxAspect: string) => (
    // The same aspect box either way, so toggling never reflows the grid above it.
    <Box
      sx={{
        mt: 2,
        aspectRatio: boxAspect,
        overflow: showTable ? 'auto' : 'visible',
        border: showTable ? `1px solid ${chart.gridline.hex}` : 'none',
        borderRadius: showTable ? 1 : 0,
      }}
    >
      {showTable ? table : chartNode}
    </Box>
  );

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
            <Typography
              variant="body2"
              color="text.secondary"
              sx={{ mt: 0.25, whiteSpace: 'pre-line' }}
            >
              {subtitle}
            </Typography>
          )}
        </Box>
        <Box sx={{ display: 'flex', alignItems: 'center', flexShrink: 0 }}>
          {/* Kept second in tab order: "View as table" is the one control every panel
              has always guaranteed reachable first (#48) — Expand is additional, not a
              replacement for it. */}
          <Button size="small" onClick={() => setShowTable((v) => !v)}>
            {showTable ? 'View as chart' : 'View as table'}
          </Button>
          <Tooltip title={`Expand ${title}`}>
            <IconButton size="small" aria-label={`Expand ${title}`} onClick={() => setExpanded(true)}>
              <OpenInFullIcon fontSize="small" />
            </IconButton>
          </Tooltip>
        </Box>
      </Box>

      {plotBox(aspect)}

      {!showTable && legend && <Box sx={{ mt: 1.5 }}>{legend}</Box>}

      {caption && (
        <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
          {caption}
        </Typography>
      )}

      {/* One-level dialog (EXPERIENCE.md's modal-depth rule) — the same chart/table
          content, just given the width a panel sharing a grid row with three others
          cannot spare. Escape and backdrop-click close it, MUI's own Dialog default. */}
      <Dialog open={expanded} onClose={() => setExpanded(false)} maxWidth="md" fullWidth>
        <DialogTitle sx={{ textAlign: 'center' }}>{title}</DialogTitle>
        <DialogContent>
          {subtitle && (
            <Typography
              variant="body2"
              color="text.secondary"
              sx={{ mb: 1, whiteSpace: 'pre-line', textAlign: 'center' }}
            >
              {subtitle}
            </Typography>
          )}
          {plotBox(aspect)}
          {!showTable && legend && <Box sx={{ mt: 1.5 }}>{legend}</Box>}
        </DialogContent>
      </Dialog>
    </Paper>
  );
}
