import Tooltip from '@mui/material/Tooltip';
import { scaleBand, scaleLinear } from 'd3-scale';

import { chart, diverging } from '../../theme/tokens';
import type { CoefficientBar } from './types';

const WIDTH = 320;
const ROW_HEIGHT = 20;
const MARGIN = { top: 8, right: 48, bottom: 8, left: 8 };
const BAR_RADIUS = 4;
/** DESIGN.md's "Coefficients / importance" family: top 20 bars shown, the rest folded
 * into a stated count rather than silently dropped. `bars` already arrives sorted by
 * magnitude, so this is a plain slice, not a re-sort. */
const TOP_N = 20;

/** `PlotPanel`'s box holds a fixed aspect ratio (`spacing.plotAspect` by default) — this
 * chart's own height instead grows and shrinks with how many bars there are, from one
 * feature up to `TOP_N`. Passing a mismatched fixed aspect either squeezes many bars
 * into too little height or, with very few bars, letterboxes a couple of short bars in
 * a mostly-empty box. The caller passes this back to `PlotPanel`'s `aspect` prop so the
 * box always matches what's actually being drawn. */
export function coefficientChartAspect(bars: CoefficientBar[]): string {
  const rows = Math.max(1, Math.min(bars.length, TOP_N));
  const height = rows * ROW_HEIGHT + MARGIN.top + MARGIN.bottom;
  return `${WIDTH} / ${height}`;
}

/**
 * DESIGN.md's "Coefficients / importance" family. Sign is real here — unlike a plain
 * importance score — so bars use the diverging ramp rather than one uniform hue, per
 * the family's stated exception for signed values.
 */
export function CoefficientChart({ bars: allBars }: { bars: CoefficientBar[] }) {
  const bars = allBars.slice(0, TOP_N);
  const folded = allBars.length - bars.length;
  const height = bars.length * ROW_HEIGHT + MARGIN.top + MARGIN.bottom;
  const plotWidth = WIDTH - MARGIN.left - MARGIN.right;
  const plotHeight = height - MARGIN.top - MARGIN.bottom;

  if (bars.length === 0) {
    return <svg role="img" aria-label="No coefficients to show." viewBox={`0 0 ${WIDTH} ${height}`} style={{ width: '100%', height: '100%' }} />;
  }

  const maxAbs = Math.max(...bars.map((b) => Math.abs(b.value)), 1e-9);
  const x = scaleLinear().domain([-maxAbs, maxAbs]).range([0, plotWidth]);
  const y = scaleBand()
    .domain(bars.map((b) => b.feature))
    .range([0, plotHeight])
    .padding(0.25);
  const zero = x(0);

  const summary = bars.map((b) => `${b.feature}: ${b.value.toFixed(3)}`).join('; ');

  return (
    <svg
      role="img"
      aria-label={`Coefficients, largest magnitude first. ${summary}.${folded > 0 ? ` And ${folded} more.` : ''}`}
      viewBox={`0 0 ${WIDTH} ${height}`}
      style={{ width: '100%', height: '100%' }}
    >
      <g transform={`translate(${MARGIN.left}, ${MARGIN.top})`}>
        <line x1={zero} x2={zero} y1={0} y2={plotHeight} stroke={chart.axis.hex} strokeWidth={1} />

        {bars.map((bar) => {
          const barY = y(bar.feature)!;
          const barX = Math.min(x(bar.value), zero);
          const barWidth = Math.max(Math.abs(x(bar.value) - zero), 1);
          const fill = bar.value >= 0 ? diverging.pos500.hex : diverging.neg500.hex;
          return (
            <Tooltip key={bar.feature} title={`${bar.feature}: ${bar.value.toFixed(3)}`} disableInteractive>
              <rect x={barX} y={barY} width={barWidth} height={y.bandwidth()} rx={BAR_RADIUS} fill={fill} />
            </Tooltip>
          );
        })}
      </g>
    </svg>
  );
}

/** Feature × value, sorted as plotted — DESIGN.md's table form for this family is
 * explicitly the full list, "not the top-20 fold". Pass the endpoint's whole `bars`
 * array here, unsliced — `CoefficientChart` is what applies the chart-only cap. */
export function coefficientRows(bars: CoefficientBar[]): { label: string; count: number }[] {
  return bars.map((b) => ({ label: b.feature, count: b.value }));
}
