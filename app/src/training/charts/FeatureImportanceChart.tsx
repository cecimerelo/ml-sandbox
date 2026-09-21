import Tooltip from '@mui/material/Tooltip';
import { scaleBand, scaleLinear } from 'd3-scale';

import { chartTooltipSx, series } from '../../theme/tokens';
import type { FeatureImportanceBar } from './types';

const WIDTH = 320;
const ROW_HEIGHT = 20;
const MARGIN = { top: 8, right: 48, bottom: 8, left: 8 };
const BAR_RADIUS = 4;
/** DESIGN.md's "Coefficients / importance" family: top 20 bars shown, the rest
 * folded into a stated count. `bars` already arrives sorted descending. */
const TOP_N = 20;

/** Same self-sizing convention as `coefficientChartAspect`. */
export function featureImportanceChartAspect(bars: FeatureImportanceBar[]): string {
  const rows = Math.max(1, Math.min(bars.length, TOP_N));
  const height = rows * ROW_HEIGHT + MARGIN.top + MARGIN.bottom;
  return `${WIDTH} / ${height}`;
}

/**
 * DESIGN.md's "Coefficients / importance" family — the unsigned case:
 * `feature_importances_` never goes negative, so unlike `CoefficientChart` this
 * never reaches for the diverging ramp. One hue (`series-1`), bars growing from
 * the left edge, length alone carrying the value.
 */
export function FeatureImportanceChart({ bars: allBars }: { bars: FeatureImportanceBar[] }) {
  const bars = allBars.slice(0, TOP_N);
  const folded = allBars.length - bars.length;
  const height = bars.length * ROW_HEIGHT + MARGIN.top + MARGIN.bottom;
  const plotWidth = WIDTH - MARGIN.left - MARGIN.right;
  const plotHeight = height - MARGIN.top - MARGIN.bottom;

  if (bars.length === 0) {
    return (
      <svg
        role="img"
        aria-label="No feature importances to show."
        viewBox={`0 0 ${WIDTH} ${height}`}
        style={{ width: '100%', height: '100%' }}
      />
    );
  }

  const maxValue = Math.max(...bars.map((b) => b.value), 1e-9);
  const x = scaleLinear().domain([0, maxValue]).range([0, plotWidth]);
  const y = scaleBand()
    .domain(bars.map((b) => b.feature))
    .range([0, plotHeight])
    .padding(0.25);

  const summary = bars.map((b) => `${b.feature}: ${b.value.toFixed(3)}`).join('; ');

  return (
    <svg
      role="img"
      aria-label={`Feature importance, largest first. ${summary}.${folded > 0 ? ` And ${folded} more.` : ''}`}
      viewBox={`0 0 ${WIDTH} ${height}`}
      style={{ width: '100%', height: '100%' }}
    >
      <g transform={`translate(${MARGIN.left}, ${MARGIN.top})`}>
        {bars.map((bar) => {
          const barY = y(bar.feature)!;
          const barWidth = Math.max(x(bar.value), 1);
          return (
            <Tooltip
              key={bar.feature}
              title={`${bar.feature}: ${bar.value.toFixed(3)}`}
              disableInteractive
              slotProps={{ tooltip: { sx: chartTooltipSx } }}
            >
              <rect x={0} y={barY} width={barWidth} height={y.bandwidth()} rx={BAR_RADIUS} fill={series[1].hex} />
            </Tooltip>
          );
        })}
      </g>
    </svg>
  );
}

/** Feature × value, sorted as plotted — the full list, same table-form contract as
 * `coefficientRows`. */
export function featureImportanceRows(
  bars: FeatureImportanceBar[],
): { label: string; count: number }[] {
  return bars.map((b) => ({ label: b.feature, count: b.value }));
}
