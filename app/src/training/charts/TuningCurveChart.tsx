import { scaleLinear } from 'd3-scale';

import { chart, series } from '../../theme/tokens';

const WIDTH = 320;
const HEIGHT = 240;
const MARGIN = { top: 16, right: 12, bottom: 24, left: 28 };
/** DESIGN.md's "Tuning curves" family: the chosen optimum gets a filled dot ≥ 8px. */
const OPTIMUM_RADIUS = 5;

export interface TuningPoint {
  x: number;
  score: number;
}

/**
 * DESIGN.md's "Tuning curves" family — accuracy-vs-K today (#99); CV-error-vs-lambda,
 * variance-explained-vs-components, and OOB error curve are the same shape and will
 * reuse this unchanged. A 2px line in series-1, the chosen hyperparameter marked with a
 * filled dot and a direct label. Bounded-metric convention: the y-axis always runs the
 * full 0-1, never a cropped range that exaggerates a small difference.
 */
export function TuningCurveChart({
  points,
  chosenX,
  xLabel,
  formatX = (x) => String(x),
}: {
  points: TuningPoint[];
  chosenX: number;
  xLabel: string;
  /** How to render the chosen value in the direct label — `K = 7`, `λ = 0.3`. */
  formatX?: (x: number) => string;
}) {
  const plotWidth = WIDTH - MARGIN.left - MARGIN.right;
  const plotHeight = HEIGHT - MARGIN.top - MARGIN.bottom;

  if (points.length === 0) {
    return (
      <svg role="img" aria-label="No tuning curve to show." viewBox={`0 0 ${WIDTH} ${HEIGHT}`} style={{ width: '100%', height: '100%' }} />
    );
  }

  const xs = points.map((p) => p.x);
  const x = scaleLinear().domain([Math.min(...xs), Math.max(...xs)]).range([0, plotWidth]);
  // Bounded-metric convention (DESIGN.md): accuracy/R²-like scores run the full 0-1.
  const y = scaleLinear().domain([0, 1]).range([plotHeight, 0]);

  const sorted = [...points].sort((a, b) => a.x - b.x);
  const linePoints = sorted.map((p) => `${x(p.x)},${y(p.score)}`).join(' ');
  const chosen = points.find((p) => p.x === chosenX);

  const summary = sorted.map((p) => `${xLabel} ${p.x}: ${p.score.toFixed(3)}`).join('; ');

  return (
    <svg
      role="img"
      aria-label={`${xLabel} tuning curve. ${summary}. Chosen: ${formatX(chosenX)}.`}
      viewBox={`0 0 ${WIDTH} ${HEIGHT}`}
      style={{ width: '100%', height: '100%' }}
    >
      <g transform={`translate(${MARGIN.left}, ${MARGIN.top})`}>
        <polyline points={linePoints} fill="none" stroke={series[1].hex} strokeWidth={2} />

        {chosen && (
          <>
            <circle cx={x(chosen.x)} cy={y(chosen.score)} r={OPTIMUM_RADIUS} fill={series[1].hex} />
            <text
              x={x(chosen.x)}
              y={y(chosen.score) - OPTIMUM_RADIUS - 4}
              fontSize={11}
              // Middle-anchored text centred on the optimum clips against the plot's own
              // edge when that point is the first or last on the curve (K's own grid
              // search picking its largest candidate is exactly this case) — the label
              // shifts to hang off whichever side still has room instead.
              textAnchor={
                x(chosen.x) < plotWidth * 0.1 ? 'start' : x(chosen.x) > plotWidth * 0.9 ? 'end' : 'middle'
              }
              fill={chart.ink.hex}
            >
              {formatX(chosen.x)}
            </text>
          </>
        )}

        <line x1={0} x2={plotWidth} y1={plotHeight} y2={plotHeight} stroke={chart.axis.hex} strokeWidth={1} />
        <line x1={0} x2={0} y1={0} y2={plotHeight} stroke={chart.axis.hex} strokeWidth={1} />
        <text x={0} y={plotHeight + 16} fontSize={11} fill={chart.inkMuted.hex}>
          {xLabel}: {Math.min(...xs)}
        </text>
        <text x={plotWidth} y={plotHeight + 16} fontSize={11} fill={chart.inkMuted.hex} textAnchor="end">
          {Math.max(...xs)}
        </text>
        <text x={4} y={-4} fontSize={11} fill={chart.inkMuted.hex}>
          Score: 1
        </text>
        <text x={4} y={plotHeight - 4} fontSize={11} fill={chart.inkMuted.hex}>
          0
        </text>
      </g>
    </svg>
  );
}

/** The plotted series as columns, x as rows — DESIGN.md's table form for this family. */
export function tuningRows(points: TuningPoint[]): { label: string; count: number }[] {
  return [...points]
    .sort((a, b) => a.x - b.x)
    .map((p) => ({ label: String(p.x), count: p.score }));
}
