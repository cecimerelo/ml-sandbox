import Tooltip from '@mui/material/Tooltip';
import { scaleLinear } from 'd3-scale';

import { chart, series } from '../theme/tokens';
import type { BoxplotSummary } from './types';

const WIDTH = 320;
const HEIGHT = 120;
const MARGIN = { top: 8, right: 24, bottom: 28, left: 24 };
const BOX_HALF_HEIGHT = 20;
const OUTLIER_RADIUS = 4;

/**
 * A single numeric column's five-number summary, drawn horizontally so it can sit at a
 * matching width beside its histogram — one series (`series-1`), the same EDA rule as
 * every other chart in this block.
 *
 * Outliers beyond Tukey's fence render as individual points; `mlsandbox.eda` already
 * decided which values those are, this only places them.
 */
export function BoxplotChart({ data }: { data: BoxplotSummary }) {
  const plotWidth = WIDTH - MARGIN.left - MARGIN.right;
  const axisY = HEIGHT - MARGIN.bottom;
  const midY = MARGIN.top + (axisY - MARGIN.top) / 2;

  const domainLow = Math.min(data.minimum, ...data.outliers);
  const domainHigh = Math.max(data.maximum, ...data.outliers);
  const x =
    domainLow === domainHigh
      ? scaleLinear().domain([domainLow - 1, domainHigh + 1]).range([0, plotWidth])
      : scaleLinear().domain([domainLow, domainHigh]).range([0, plotWidth]);

  const label =
    `min ${data.minimum.toFixed(1)}, Q1 ${data.q1.toFixed(1)}, median ${data.median.toFixed(1)}, ` +
    `Q3 ${data.q3.toFixed(1)}, max ${data.maximum.toFixed(1)}` +
    (data.outliers.length > 0 ? `, ${data.outliers.length} outlier(s)` : '');

  return (
    <svg
      role="img"
      aria-label={`Boxplot. ${label}.`}
      viewBox={`0 0 ${WIDTH} ${HEIGHT}`}
      style={{ width: '100%', height: '100%' }}
    >
      {/* Whisker */}
      <line
        x1={MARGIN.left + x(data.minimum)}
        x2={MARGIN.left + x(data.maximum)}
        y1={midY}
        y2={midY}
        stroke={chart.axis.hex}
        strokeWidth={1}
      />
      <line
        x1={MARGIN.left + x(data.minimum)}
        x2={MARGIN.left + x(data.minimum)}
        y1={midY - BOX_HALF_HEIGHT / 2}
        y2={midY + BOX_HALF_HEIGHT / 2}
        stroke={chart.axis.hex}
        strokeWidth={1}
      />
      <line
        x1={MARGIN.left + x(data.maximum)}
        x2={MARGIN.left + x(data.maximum)}
        y1={midY - BOX_HALF_HEIGHT / 2}
        y2={midY + BOX_HALF_HEIGHT / 2}
        stroke={chart.axis.hex}
        strokeWidth={1}
      />

      {/* Box */}
      <Tooltip
        title={`Q1 ${data.q1.toFixed(1)} to Q3 ${data.q3.toFixed(1)}`}
        disableInteractive
      >
        <rect
          x={MARGIN.left + x(data.q1)}
          y={midY - BOX_HALF_HEIGHT}
          width={Math.max(x(data.q3) - x(data.q1), 1)}
          height={BOX_HALF_HEIGHT * 2}
          fill={series[1].hex}
          fillOpacity={0.35}
          stroke={series[1].hex}
          strokeWidth={2}
        />
      </Tooltip>

      {/* Median */}
      <Tooltip title={`Median ${data.median.toFixed(1)}`} disableInteractive>
        <line
          x1={MARGIN.left + x(data.median)}
          x2={MARGIN.left + x(data.median)}
          y1={midY - BOX_HALF_HEIGHT}
          y2={midY + BOX_HALF_HEIGHT}
          stroke={series[1].hex}
          strokeWidth={2}
        />
      </Tooltip>

      {/* Outliers */}
      {data.outliers.map((value, i) => (
        <Tooltip key={i} title={`Outlier: ${value.toFixed(1)}`} disableInteractive>
          <circle
            cx={MARGIN.left + x(value)}
            cy={midY}
            r={OUTLIER_RADIUS}
            fill="none"
            stroke={series[1].hex}
            strokeWidth={1.5}
          />
        </Tooltip>
      ))}

      {/* Axis rule and the range's two endpoints — the same convention as the
          histogram's x-axis: enough to read the scale without a full tick ladder. */}
      <line
        x1={MARGIN.left}
        x2={MARGIN.left + plotWidth}
        y1={axisY}
        y2={axisY}
        stroke={chart.axis.hex}
        strokeWidth={1}
      />
      <text x={MARGIN.left} y={axisY + 16} fontSize={11} fill={chart.inkMuted.hex}>
        {domainLow.toFixed(1)}
      </text>
      <text
        x={MARGIN.left + plotWidth}
        y={axisY + 16}
        fontSize={11}
        fill={chart.inkMuted.hex}
        textAnchor="end"
      >
        {domainHigh.toFixed(1)}
      </text>
    </svg>
  );
}

/** The five-number summary, plus a row per outlier — the table form for a boxplot. */
export function boxplotRows(data: BoxplotSummary): { label: string; count: number }[] {
  const rows = [
    { label: 'Minimum', count: data.minimum },
    { label: 'Q1', count: data.q1 },
    { label: 'Median', count: data.median },
    { label: 'Q3', count: data.q3 },
    { label: 'Maximum', count: data.maximum },
  ];
  return [
    ...rows,
    ...data.outliers.map((value, i) => ({ label: `Outlier ${i + 1}`, count: value })),
  ];
}
