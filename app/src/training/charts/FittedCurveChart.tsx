import Tooltip from '@mui/material/Tooltip';
import { scaleLinear } from 'd3-scale';

import { chart, chartTooltipSx, series } from '../../theme/tokens';
import type { ScatterPoint } from './types';

const WIDTH = 320;
const HEIGHT = 240;
const MARGIN = { top: 8, right: 8, bottom: 24, left: 32 };
/** DESIGN.md's scatter mark spec: dots ≥ 8px diameter. */
const DOT_RADIUS = 4;

/**
 * DESIGN.md's "Actual-vs-predicted pairs" family, applied to one feature at a time:
 * the real (feature, target) rows in `chart-ink-muted` (ground truth, not a
 * competing series), the pipeline's own fitted curve in `series-1` as that one
 * feature sweeps its observed range with every other feature held fixed — the same
 * one-axis-at-a-time reading `DecisionBoundaryChart` already gives a classifier.
 */
export function FittedCurveChart({
  feature,
  curve,
  actual,
}: {
  feature: string;
  curve: ScatterPoint[];
  actual: ScatterPoint[];
}) {
  const plotWidth = WIDTH - MARGIN.left - MARGIN.right;
  const plotHeight = HEIGHT - MARGIN.top - MARGIN.bottom;

  if (curve.length === 0) {
    return (
      <svg
        role="img"
        aria-label="No numeric column to plot a fitted curve against."
        viewBox={`0 0 ${WIDTH} ${HEIGHT}`}
        style={{ width: '100%', height: '100%' }}
      />
    );
  }

  const allPoints = [...curve, ...actual];
  const xs = allPoints.map((p) => p.x);
  const ys = allPoints.map((p) => p.y);
  const x = scaleLinear().domain([Math.min(...xs), Math.max(...xs)]).range([0, plotWidth]);
  const y = scaleLinear().domain([Math.min(...ys), Math.max(...ys)]).range([plotHeight, 0]);

  const sortedCurve = [...curve].sort((a, b) => a.x - b.x);
  const linePoints = sortedCurve.map((p) => `${x(p.x)},${y(p.y)}`).join(' ');

  return (
    <svg
      role="img"
      aria-label={`Fitted curve over ${feature}, with the real rows plotted for comparison.`}
      viewBox={`0 0 ${WIDTH} ${HEIGHT}`}
      style={{ width: '100%', height: '100%' }}
    >
      <g transform={`translate(${MARGIN.left}, ${MARGIN.top})`}>
        {actual.map((point, i) => (
          <Tooltip
            key={i}
            title={`${feature} ${point.x.toFixed(1)}, actual ${point.y.toFixed(1)}`}
            disableInteractive
            slotProps={{ tooltip: { sx: chartTooltipSx } }}
          >
            <circle
              cx={x(point.x)}
              cy={y(point.y)}
              r={DOT_RADIUS}
              fill={chart.inkMuted.hex}
              fillOpacity={0.5}
            />
          </Tooltip>
        ))}

        <polyline points={linePoints} fill="none" stroke={series[1].hex} strokeWidth={2} />

        <line x1={0} x2={plotWidth} y1={plotHeight} y2={plotHeight} stroke={chart.axis.hex} strokeWidth={1} />
        <line x1={0} x2={0} y1={0} y2={plotHeight} stroke={chart.axis.hex} strokeWidth={1} />
        <text x={0} y={plotHeight + 16} fontSize={11} fill={chart.inkMuted.hex}>
          {feature}: {Math.min(...xs).toFixed(1)}
        </text>
        <text x={plotWidth} y={plotHeight + 16} fontSize={11} fill={chart.inkMuted.hex} textAnchor="end">
          {Math.max(...xs).toFixed(1)}
        </text>
      </g>
    </svg>
  );
}
