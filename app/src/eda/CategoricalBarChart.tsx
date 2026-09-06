import Tooltip from '@mui/material/Tooltip';
import { scaleBand, scaleLinear } from 'd3-scale';
import { useState } from 'react';

import { chart, series } from '../theme/tokens';
import type { CategoricalBars } from './types';

const WIDTH = 320;
const ROW_HEIGHT = 28;
const MARGIN = { top: 4, right: 40, bottom: 4, left: 96 };
const BAR_RADIUS = 4;

/**
 * One categorical column's bar chart. Horizontal, sorted frequency-descending (already
 * the order `mlsandbox.eda` returns), so long category labels have room to sit beside
 * their bar rather than rotated under it.
 *
 * The tail beyond the top 15 is not here — `mlsandbox.eda` already folded it into
 * `other_count` — this component only draws the "Other (N categories)" bar the fold
 * produces, in `series-other`, never a real series colour.
 */
export function CategoricalBarChart({ data }: { data: CategoricalBars }) {
  const [hovered, setHovered] = useState<number | null>(null);

  const rows = [
    ...data.categories.map((c) => ({ label: c.category, count: c.count, folded: false })),
    ...(data.other_categories > 0
      ? [
          {
            label: `Other (${data.other_categories} categories)`,
            count: data.other_count,
            folded: true,
          },
        ]
      : []),
  ];

  const plotWidth = WIDTH - MARGIN.left - MARGIN.right;
  const height = rows.length * ROW_HEIGHT + MARGIN.top + MARGIN.bottom;

  const maxCount = Math.max(...rows.map((r) => r.count), 1);
  const x = scaleLinear().domain([0, maxCount]).range([0, plotWidth]);
  const y = scaleBand()
    .domain(rows.map((_, i) => String(i)))
    .range([0, rows.length * ROW_HEIGHT])
    .padding(0.2);

  const summary = rows.map((r) => `${r.label}: ${r.count}`).join('; ');

  return (
    <svg
      role="img"
      aria-label={`Bar chart of ${data.column}. ${summary}.`}
      viewBox={`0 0 ${WIDTH} ${height}`}
      style={{ width: '100%', height: '100%' }}
      preserveAspectRatio="xMidYMid meet"
    >
      <g transform={`translate(${MARGIN.left}, ${MARGIN.top})`}>
        {rows.map((row, i) => {
          const barY = y(String(i))!;
          const barHeight = y.bandwidth();
          const barWidth = Math.max(x(row.count), 0);
          const label = `${row.label}: ${row.count}`;
          return (
            <g key={i}>
              <text
                x={-8}
                y={barY + barHeight / 2}
                fontSize={11}
                fill={chart.ink.hex}
                textAnchor="end"
                dominantBaseline="middle"
              >
                {row.label.length > 14 ? `${row.label.slice(0, 13)}…` : row.label}
              </text>
              <Tooltip title={label} disableInteractive>
                <rect
                  x={0}
                  y={barY}
                  width={barWidth}
                  height={barHeight}
                  rx={BAR_RADIUS}
                  fill={row.folded ? series.other.hex : series[1].hex}
                  opacity={hovered === null || hovered === i ? 1 : 0.5}
                  onMouseEnter={() => setHovered(i)}
                  onMouseLeave={() => setHovered(null)}
                />
              </Tooltip>
              <text
                x={barWidth + 6}
                y={barY + barHeight / 2}
                fontSize={11}
                fill={chart.inkMuted.hex}
                dominantBaseline="middle"
              >
                {row.count}
              </text>
            </g>
          );
        })}
      </g>
    </svg>
  );
}

/** Category × count — the table form DESIGN.md specifies for categorical bars. */
export function categoricalRows(data: CategoricalBars): { label: string; count: number }[] {
  return [
    ...data.categories.map((c) => ({ label: c.category, count: c.count })),
    ...(data.other_categories > 0
      ? [{ label: `Other (${data.other_categories} categories)`, count: data.other_count }]
      : []),
  ];
}
