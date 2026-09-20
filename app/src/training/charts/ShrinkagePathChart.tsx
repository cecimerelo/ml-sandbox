import Tooltip from '@mui/material/Tooltip';
import { scaleLog, scaleLinear } from 'd3-scale';

import { chart, series } from '../../theme/tokens';
import type { ShrinkagePoint } from './types';

const WIDTH = 320;
const HEIGHT = 240;
const MARGIN = { top: 16, right: 12, bottom: 24, left: 28 };
/** DESIGN.md's "Shrinkage paths" family: everything not promoted stays this faint. */
const MUTED_OPACITY = 0.4;

interface FeatureLine {
  feature: string;
  points: { x: number; coefficient: number }[];
}

function groupByFeature(points: ShrinkagePoint[]): FeatureLine[] {
  const byFeature = new Map<string, { x: number; coefficient: number }[]>();
  for (const p of points) {
    const line = byFeature.get(p.feature) ?? [];
    line.push({ x: p.x, coefficient: p.coefficient });
    byFeature.set(p.feature, line);
  }
  return [...byFeature.entries()].map(([feature, pts]) => ({
    feature,
    points: pts.sort((a, b) => a.x - b.x),
  }));
}

/**
 * DESIGN.md's "Shrinkage paths" family — the one family that exceeds 4 series. Every
 * feature's coefficient path is drawn in `chart-ink-muted` at 40% opacity; the 3
 * largest-magnitude coefficients at the chosen regularization strength promote to
 * `series-1`/`series-2`/`series-3` at full opacity. The name is on hover, not a
 * standing direct label: shrinkage converges every path toward similar values at the
 * strong end of the path, so labels planted there print on top of each other rather
 * than beside distinct lines. The x-axis (α or C) spans several orders of magnitude
 * by construction — the grid `RidgeCV`/`LassoCV`/`LogisticRegressionCV` explored
 * their own alpha/C candidates across — so it runs on a log scale, or a genuinely
 * varying curve reads as a handful of points bunched against the left edge.
 */
export function ShrinkagePathChart({
  points,
  promotedFeatures,
  xLabel,
}: {
  points: ShrinkagePoint[];
  promotedFeatures: string[];
  xLabel: string;
}) {
  const plotWidth = WIDTH - MARGIN.left - MARGIN.right;
  const plotHeight = HEIGHT - MARGIN.top - MARGIN.bottom;

  if (points.length === 0) {
    return (
      <svg
        role="img"
        aria-label="No shrinkage path to show."
        viewBox={`0 0 ${WIDTH} ${HEIGHT}`}
        style={{ width: '100%', height: '100%' }}
      />
    );
  }

  const lines = groupByFeature(points);
  const xs = points.map((p) => p.x);
  const maxAbsCoefficient = Math.max(...points.map((p) => Math.abs(p.coefficient)), 1e-9);

  const x = scaleLog().domain([Math.min(...xs), Math.max(...xs)]).range([0, plotWidth]);
  const y = scaleLinear()
    .domain([-maxAbsCoefficient, maxAbsCoefficient])
    .range([plotHeight, 0]);
  const zero = y(0);

  const promoted = new Set(promotedFeatures);
  const promotedColor = new Map(promotedFeatures.map((feature, i) => [feature, series[(i + 1) as 1 | 2 | 3].hex]));

  const summary = lines
    .map((line) => `${line.feature}: ${line.points[line.points.length - 1]?.coefficient.toFixed(3) ?? 'n/a'}`)
    .join('; ');

  return (
    <svg
      role="img"
      aria-label={`Coefficient shrinkage path by ${xLabel}. Ending values: ${summary}. Largest magnitude: ${promotedFeatures.join(', ')}.`}
      viewBox={`0 0 ${WIDTH} ${HEIGHT}`}
      style={{ width: '100%', height: '100%' }}
    >
      <g transform={`translate(${MARGIN.left}, ${MARGIN.top})`}>
        <line x1={0} x2={plotWidth} y1={zero} y2={zero} stroke={chart.axis.hex} strokeWidth={1} />
        <line x1={0} x2={0} y1={0} y2={plotHeight} stroke={chart.axis.hex} strokeWidth={1} />

        {lines
          .filter((line) => !promoted.has(line.feature))
          .map((line) => {
            const linePoints = line.points.map((p) => `${x(p.x)},${y(p.coefficient)}`).join(' ');
            const last = line.points[line.points.length - 1];
            return (
              <Tooltip
                key={line.feature}
                title={`${line.feature}: ${last?.coefficient.toFixed(3) ?? 'n/a'}`}
                disableInteractive
              >
                <g>
                  {/* A transparent, wider stroke widens the hoverable hit area past the
                      1px visible line — hovering a hairline precisely is otherwise hard. */}
                  <polyline points={linePoints} fill="none" stroke="transparent" strokeWidth={10} />
                  <polyline
                    points={linePoints}
                    fill="none"
                    stroke={chart.inkMuted.hex}
                    strokeOpacity={MUTED_OPACITY}
                    strokeWidth={1}
                  />
                </g>
              </Tooltip>
            );
          })}

        {lines
          .filter((line) => promoted.has(line.feature))
          .map((line) => {
            const color = promotedColor.get(line.feature)!;
            const linePoints = line.points.map((p) => `${x(p.x)},${y(p.coefficient)}`).join(' ');
            const last = line.points[line.points.length - 1];
            return (
              <Tooltip
                key={line.feature}
                title={`${line.feature}: ${last?.coefficient.toFixed(3) ?? 'n/a'}`}
                disableInteractive
              >
                <g>
                  <polyline points={linePoints} fill="none" stroke="transparent" strokeWidth={10} />
                  <polyline points={linePoints} fill="none" stroke={color} strokeWidth={2} />
                </g>
              </Tooltip>
            );
          })}

        <text x={0} y={plotHeight + 16} fontSize={11} fill={chart.inkMuted.hex}>
          {xLabel}: {Math.min(...xs).toPrecision(2)}
        </text>
        <text x={plotWidth} y={plotHeight + 16} fontSize={11} fill={chart.inkMuted.hex} textAnchor="end">
          {Math.max(...xs).toPrecision(2)}
        </text>
        <text x={4} y={8} fontSize={11} fill={chart.inkMuted.hex}>
          {maxAbsCoefficient.toFixed(2)}
        </text>
        <text x={4} y={plotHeight - 4} fontSize={11} fill={chart.inkMuted.hex}>
          -{maxAbsCoefficient.toFixed(2)}
        </text>
      </g>
    </svg>
  );
}

/** Feature × coefficient at the largest regularization strength plotted — DESIGN.md's
 * table form for this family: "the plotted series as columns, x as rows", downsampled
 * here to each feature's value at that one end of the path rather than every (feature,
 * x) pair, since that full cross product is what the chart itself already renders. */
export function shrinkageRows(points: ShrinkagePoint[]): { label: string; count: number }[] {
  return groupByFeature(points)
    .map((line) => ({ label: line.feature, count: line.points[line.points.length - 1]!.coefficient }))
    .sort((a, b) => Math.abs(b.count) - Math.abs(a.count));
}
