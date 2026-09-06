import Tooltip from '@mui/material/Tooltip';
import { scaleLinear } from 'd3-scale';
import { useState } from 'react';

import { chart, series } from '../theme/tokens';
import type { Histogram } from './types';

const WIDTH = 320;
const HEIGHT = 240;
const MARGIN = { top: 8, right: 8, bottom: 24, left: 8 };
const GAP = 2;
/** Bars get a radius only on the value end, never at the baseline (DESIGN.md mark spec). */
const BAR_RADIUS = 4;

/**
 * One numeric column's histogram. One series (`series-1`) — a histogram does not need
 * four colours, per DESIGN.md's EDA row.
 *
 * A fixed-viewBox SVG that scales to its container via `width="100%"`, so the surrounding
 * `PlotPanel`'s aspect box, not this component, owns the actual rendered size.
 */
export function HistogramChart({ data }: { data: Histogram }) {
  const [hovered, setHovered] = useState<number | null>(null);
  const plotWidth = WIDTH - MARGIN.left - MARGIN.right;
  const plotHeight = HEIGHT - MARGIN.top - MARGIN.bottom;

  if (data.bins.length === 0) {
    return (
      <svg
        role="img"
        aria-label={`${data.column}: no values to show, all missing.`}
        viewBox={`0 0 ${WIDTH} ${HEIGHT}`}
        style={{ width: '100%', height: '100%' }}
      />
    );
  }

  const x = scaleLinear()
    .domain([data.bins[0]!.start, data.bins[data.bins.length - 1]!.end])
    .range([0, plotWidth]);
  // Bar charts always start at zero (DESIGN.md mark spec).
  const maxCount = Math.max(...data.bins.map((b) => b.count));
  const y = scaleLinear().domain([0, maxCount || 1]).range([plotHeight, 0]);

  const summary = data.bins
    .map((b) => `${b.start.toFixed(1)} to ${b.end.toFixed(1)}: ${b.count}`)
    .join('; ');

  return (
    <svg
      role="img"
      aria-label={`Histogram of ${data.column}. ${summary}.`}
      viewBox={`0 0 ${WIDTH} ${HEIGHT}`}
      style={{ width: '100%', height: '100%' }}
    >
      <g transform={`translate(${MARGIN.left}, ${MARGIN.top})`}>
        {/* Horizontal gridlines only — recessive, the marks are the content. */}
        {[0, 0.5, 1].map((t) => (
          <line
            key={t}
            x1={0}
            x2={plotWidth}
            y1={y(maxCount * t)}
            y2={y(maxCount * t)}
            stroke={chart.gridline.hex}
            strokeWidth={1}
          />
        ))}

        {data.bins.map((bin, i) => {
          const barX = x(bin.start) + GAP / 2;
          const barWidth = Math.max(x(bin.end) - x(bin.start) - GAP, 0);
          const barY = y(bin.count);
          const barHeight = plotHeight - barY;
          const label = `${bin.start.toFixed(1)}–${bin.end.toFixed(1)}: ${bin.count}`;
          return (
            <Tooltip key={i} title={label} disableInteractive>
              <rect
                x={barX}
                y={barHeight === 0 ? plotHeight : barY}
                width={barWidth}
                height={barHeight}
                rx={BAR_RADIUS}
                fill={series[1].hex}
                opacity={hovered === null || hovered === i ? 1 : 0.5}
                onMouseEnter={() => setHovered(i)}
                onMouseLeave={() => setHovered(null)}
              />
            </Tooltip>
          );
        })}

        {/* Axis rule and the range's two endpoints — enough to read the scale without
            cluttering a panel this small with a full tick ladder. */}
        <line
          x1={0}
          x2={plotWidth}
          y1={plotHeight}
          y2={plotHeight}
          stroke={chart.axis.hex}
          strokeWidth={1}
        />
        <text x={0} y={plotHeight + 16} fontSize={11} fill={chart.inkMuted.hex}>
          {data.bins[0]!.start.toFixed(1)}
        </text>
        <text
          x={plotWidth}
          y={plotHeight + 16}
          fontSize={11}
          fill={chart.inkMuted.hex}
          textAnchor="end"
        >
          {data.bins[data.bins.length - 1]!.end.toFixed(1)}
        </text>
      </g>
    </svg>
  );
}

/** Bin × count — the table form DESIGN.md specifies for histograms. */
export function histogramRows(data: Histogram): { label: string; count: number }[] {
  return data.bins.map((b) => ({ label: `${b.start.toFixed(1)}–${b.end.toFixed(1)}`, count: b.count }));
}
