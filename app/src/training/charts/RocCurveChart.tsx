import { scaleLinear } from 'd3-scale';

import { chart, series } from '../../theme/tokens';
import type { RocPoint } from './types';

const WIDTH = 320;
const HEIGHT = 240;
const MARGIN = { top: 8, right: 8, bottom: 24, left: 28 };

/**
 * DESIGN.md's "Classification quality" family: one line in `series-1`, plus a dashed
 * `chart-axis` chance diagonal — a model no better than a coin flip sits on that line.
 */
export function RocCurveChart({ points, auc: aucValue }: { points: RocPoint[]; auc: number }) {
  const plotWidth = WIDTH - MARGIN.left - MARGIN.right;
  const plotHeight = HEIGHT - MARGIN.top - MARGIN.bottom;

  const x = scaleLinear().domain([0, 1]).range([0, plotWidth]);
  const y = scaleLinear().domain([0, 1]).range([plotHeight, 0]);
  const polylinePoints = points
    .map((p) => `${x(p.false_positive_rate)},${y(p.true_positive_rate)}`)
    .join(' ');

  return (
    <svg
      role="img"
      aria-label={`ROC curve, area under the curve ${aucValue.toFixed(3)}.`}
      viewBox={`0 0 ${WIDTH} ${HEIGHT}`}
      style={{ width: '100%', height: '100%' }}
    >
      <g transform={`translate(${MARGIN.left}, ${MARGIN.top})`}>
        <line x1={x(0)} x2={x(1)} y1={y(0)} y2={y(1)} stroke={chart.axis.hex} strokeWidth={2} strokeDasharray="6 4" />
        {points.length > 0 && (
          <polyline points={polylinePoints} fill="none" stroke={series[1].hex} strokeWidth={2} />
        )}

        <line x1={0} x2={plotWidth} y1={plotHeight} y2={plotHeight} stroke={chart.axis.hex} strokeWidth={1} />
        <line x1={0} x2={0} y1={0} y2={plotHeight} stroke={chart.axis.hex} strokeWidth={1} />
        <text x={0} y={plotHeight + 16} fontSize={11} fill={chart.inkMuted.hex}>
          False positive rate: 0
        </text>
        <text x={plotWidth} y={plotHeight + 16} fontSize={11} fill={chart.inkMuted.hex} textAnchor="end">
          1
        </text>
        <text x={-MARGIN.left + 4} y={12} fontSize={11} fill={chart.inkMuted.hex}>
          True positive rate: 1
        </text>
        <text x={-MARGIN.left + 4} y={plotHeight - 4} fontSize={11} fill={chart.inkMuted.hex}>
          0
        </text>
      </g>
    </svg>
  );
}

/** The plotted series as columns, x as rows — DESIGN.md's table form for this family.
 * Downsampled to at most 100 rows, stated as such by the caller's subtitle/caption. */
export function rocRows(points: RocPoint[]): { label: string; count: number }[] {
  const step = Math.max(1, Math.ceil(points.length / 100));
  return points
    .filter((_, i) => i % step === 0)
    .map((p) => ({
      label: p.false_positive_rate.toFixed(3),
      count: p.true_positive_rate,
    }));
}
