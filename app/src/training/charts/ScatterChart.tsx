import Tooltip from '@mui/material/Tooltip';
import { scaleLinear } from 'd3-scale';

import { chart, series } from '../../theme/tokens';

const WIDTH = 320;
const HEIGHT = 240;
const MARGIN = { top: 8, right: 8, bottom: 24, left: 8 };
/** DESIGN.md's scatter mark spec: dots ≥ 8px diameter. */
const DOT_RADIUS = 5;
/** The 2px white ring that keeps overlapping points countable. */
const RING_WIDTH = 2;

/**
 * Enough decimals that a small-magnitude axis (leverage often sits in the 0.01-0.05
 * range) doesn't round both endpoints to the same displayed value — `toFixed(1)` alone
 * once showed a leverage axis as "0.0" to "0.0", two genuinely different numbers made
 * to look identical.
 */
function formatTick(value: number): string {
  const magnitude = Math.abs(value);
  if (magnitude === 0) return '0';
  if (magnitude < 0.01) return value.toExponential(1);
  if (magnitude < 1) return value.toFixed(3);
  return value.toFixed(1);
}

/**
 * The "Fit / residual" family's shared scatter form (DESIGN.md): marks in `series-1` at
 * 60% opacity, a 2px dashed neutral reference line (never coloured — it is not a series).
 *
 * One component for residual, predicted-vs-actual, and leverage plots — they differ only
 * in what the reference line means (`zero`: y = 0, `diagonal`: y = x) and their axis
 * labels, not in how a point or the reference line is drawn.
 */
export function ScatterChart({
  points,
  reference,
  xLabel,
  yLabel,
  ariaLabel,
  pointLabel,
}: {
  points: { x: number; y: number }[];
  reference: 'zero' | 'diagonal';
  xLabel: string;
  yLabel: string;
  ariaLabel: string;
  pointLabel: (point: { x: number; y: number }) => string;
}) {
  const plotWidth = WIDTH - MARGIN.left - MARGIN.right;
  const plotHeight = HEIGHT - MARGIN.top - MARGIN.bottom;

  if (points.length === 0) {
    return <svg role="img" aria-label={`${ariaLabel} No points to show.`} viewBox={`0 0 ${WIDTH} ${HEIGHT}`} style={{ width: '100%', height: '100%' }} />;
  }

  const xs = points.map((p) => p.x);
  const ys = points.map((p) => p.y);
  let xLo = Math.min(...xs);
  let xHi = Math.max(...xs);
  let yLo = Math.min(...ys);
  let yHi = Math.max(...ys);

  if (reference === 'diagonal') {
    // The y = x line only reads as a diagonal if both axes share one domain.
    const lo = Math.min(xLo, yLo);
    const hi = Math.max(xHi, yHi);
    xLo = yLo = lo;
    xHi = yHi = hi;
  } else if (yLo === yHi) {
    // A dead-flat set of residuals still needs room to draw the y = 0 reference line.
    yLo = Math.min(0, yLo - 1);
    yHi = Math.max(0, yHi + 1);
  }
  if (xLo === xHi) {
    xLo -= 1;
    xHi += 1;
  }

  const x = scaleLinear().domain([xLo, xHi]).range([0, plotWidth]);
  const y = scaleLinear().domain([yLo, yHi]).range([plotHeight, 0]);

  return (
    <svg role="img" aria-label={ariaLabel} viewBox={`0 0 ${WIDTH} ${HEIGHT}`} style={{ width: '100%', height: '100%' }}>
      <g transform={`translate(${MARGIN.left}, ${MARGIN.top})`}>
        {reference === 'zero' ? (
          <line x1={0} x2={plotWidth} y1={y(0)} y2={y(0)} stroke={chart.axis.hex} strokeWidth={2} strokeDasharray="6 4" />
        ) : (
          <line x1={x(xLo)} x2={x(xHi)} y1={y(xLo)} y2={y(xHi)} stroke={chart.axis.hex} strokeWidth={2} strokeDasharray="6 4" />
        )}

        {points.map((point, i) => (
          <Tooltip key={i} title={pointLabel(point)} disableInteractive>
            <circle
              cx={x(point.x)}
              cy={y(point.y)}
              r={DOT_RADIUS}
              fill={series[1].hex}
              fillOpacity={0.6}
              stroke="#ffffff"
              strokeWidth={RING_WIDTH}
            />
          </Tooltip>
        ))}

        <line x1={0} x2={plotWidth} y1={plotHeight} y2={plotHeight} stroke={chart.axis.hex} strokeWidth={1} />
        <line x1={0} x2={0} y1={0} y2={plotHeight} stroke={chart.axis.hex} strokeWidth={1} />

        {/* Each axis gets its name once plus its two endpoints — enough to read the
            scale without a full tick ladder, the same convention as the EDA charts. */}
        <text x={0} y={plotHeight + 16} fontSize={11} fill={chart.inkMuted.hex}>
          {xLabel}: {formatTick(xLo)}
        </text>
        <text x={plotWidth} y={plotHeight + 16} fontSize={11} fill={chart.inkMuted.hex} textAnchor="end">
          {formatTick(xHi)}
        </text>
        <text x={4} y={12} fontSize={11} fill={chart.inkMuted.hex}>
          {yLabel}: {formatTick(yHi)}
        </text>
        <text x={4} y={plotHeight - 4} fontSize={11} fill={chart.inkMuted.hex}>
          {formatTick(yLo)}
        </text>
      </g>
    </svg>
  );
}

/** n, mean, SD, min/max — the table form DESIGN.md specifies for this family: summary
 * statistics, never the raw point cloud. */
export function scatterSummaryRows(
  points: { x: number; y: number }[],
  valueOf: (point: { x: number; y: number }) => number
): { label: string; count: number }[] {
  const values = points.map(valueOf);
  const n = values.length;
  if (n === 0) return [{ label: 'n', count: 0 }];
  const mean = values.reduce((a, b) => a + b, 0) / n;
  const variance = values.reduce((a, b) => a + (b - mean) ** 2, 0) / n;
  return [
    { label: 'n', count: n },
    { label: 'Mean', count: mean },
    { label: 'SD', count: Math.sqrt(variance) },
    { label: 'Minimum', count: Math.min(...values) },
    { label: 'Maximum', count: Math.max(...values) },
  ];
}
