import { scaleLinear } from 'd3-scale';

import { chart, series } from '../../theme/tokens';
import type { ComponentPoint } from './types';

const WIDTH = 320;
const HEIGHT = 240;
const MARGIN = { top: 16, right: 12, bottom: 24, left: 28 };
/** DESIGN.md's "Tuning curves" family: the chosen optimum gets a filled dot ≥ 8px. */
const OPTIMUM_RADIUS = 5;

/**
 * DESIGN.md's "Tuning curves" family: cumulative variance explained as component
 * count grows. `x_variance` (predictors) is always drawn; `y_variance` (target) only
 * exists for PLS — PCA never sees the target — so a second `series-2` line appears
 * only when the data has it. Bounded-metric convention: the y-axis always runs the
 * full 0-1, both curves converging toward it as more components are kept.
 */
export function VarianceExplainedChart({
  points,
  chosenX,
  xLabel,
}: {
  points: ComponentPoint[];
  chosenX: number;
  xLabel: string;
}) {
  const plotWidth = WIDTH - MARGIN.left - MARGIN.right;
  const plotHeight = HEIGHT - MARGIN.top - MARGIN.bottom;

  if (points.length === 0) {
    return (
      <svg
        role="img"
        aria-label="No variance-explained curve to show."
        viewBox={`0 0 ${WIDTH} ${HEIGHT}`}
        style={{ width: '100%', height: '100%' }}
      />
    );
  }

  const hasYVariance = points.some((p) => p.y_variance !== null);
  const sorted = [...points].sort((a, b) => a.x - b.x);
  const xs = sorted.map((p) => p.x);
  const x = scaleLinear().domain([Math.min(...xs), Math.max(...xs)]).range([0, plotWidth]);
  const y = scaleLinear().domain([0, 1]).range([plotHeight, 0]);

  const xLine = sorted.map((p) => `${x(p.x)},${y(p.x_variance)}`).join(' ');
  const yLine = hasYVariance
    ? sorted.map((p) => `${x(p.x)},${y(p.y_variance ?? 0)}`).join(' ')
    : null;
  const chosen = sorted.find((p) => p.x === chosenX);
  const lastX = sorted[sorted.length - 1];
  const lastY = hasYVariance ? sorted[sorted.length - 1] : null;
  const anchor = x((lastX?.x ?? 0)) > plotWidth * 0.7 ? 'end' : 'start';

  const summary = sorted
    .map((p) => `${xLabel} ${p.x}: predictors ${p.x_variance.toFixed(3)}${p.y_variance !== null ? `, target ${p.y_variance.toFixed(3)}` : ''}`)
    .join('; ');

  return (
    <svg
      role="img"
      aria-label={`Variance explained by ${xLabel}. ${summary}. Chosen: ${xLabel} = ${chosenX}.`}
      viewBox={`0 0 ${WIDTH} ${HEIGHT}`}
      style={{ width: '100%', height: '100%' }}
    >
      <g transform={`translate(${MARGIN.left}, ${MARGIN.top})`}>
        <polyline points={xLine} fill="none" stroke={series[1].hex} strokeWidth={2} />
        {yLine && <polyline points={yLine} fill="none" stroke={series[2].hex} strokeWidth={2} />}

        {lastX && (
          <text x={x(lastX.x)} y={y(lastX.x_variance) - 6} fontSize={11} textAnchor={anchor} fill={series[1].hex}>
            predictors
          </text>
        )}
        {lastY && lastY.y_variance !== null && (
          <text x={x(lastY.x)} y={y(lastY.y_variance) - 6} fontSize={11} textAnchor={anchor} fill={series[2].hex}>
            target
          </text>
        )}

        {chosen && (
          <>
            <circle cx={x(chosen.x)} cy={y(chosen.x_variance)} r={OPTIMUM_RADIUS} fill={series[1].hex} />
            {chosen.y_variance !== null && (
              <circle cx={x(chosen.x)} cy={y(chosen.y_variance)} r={OPTIMUM_RADIUS} fill={series[2].hex} />
            )}
          </>
        )}

        <line x1={0} x2={plotWidth} y1={plotHeight} y2={plotHeight} stroke={chart.axis.hex} strokeWidth={1} />
        <line x1={0} x2={0} y1={0} y2={plotHeight} stroke={chart.axis.hex} strokeWidth={1} />
        <text x={0} y={plotHeight + 16} fontSize={11} fill={chart.inkMuted.hex}>
          {xLabel}: {Math.min(...xs)}
        </text>
        <text x={plotWidth} y={plotHeight + 16} fontSize={11} fill={chart.inkMuted.hex} textAnchor="end">
          {Math.max(...xs)} — chosen: {chosenX}
        </text>
        <text x={4} y={-4} fontSize={11} fill={chart.inkMuted.hex}>
          Variance: 1
        </text>
        <text x={4} y={plotHeight - 4} fontSize={11} fill={chart.inkMuted.hex}>
          0
        </text>
      </g>
    </svg>
  );
}

/** The plotted series as columns, x as rows — DESIGN.md's table form for this family. */
export function varianceExplainedRows(
  points: ComponentPoint[],
): { label: string; count: number }[] {
  return [...points]
    .sort((a, b) => a.x - b.x)
    .map((p) => ({ label: String(p.x), count: p.x_variance }));
}
