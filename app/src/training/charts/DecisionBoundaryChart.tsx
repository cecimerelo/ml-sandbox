import Grid from '@mui/material/Grid';
import Typography from '@mui/material/Typography';
import { scaleLinear } from 'd3-scale';

import { chart, series } from '../../theme/tokens';
import type { BoundaryCell, DecisionBoundary } from './types';

const SIZE = 320;
/** DESIGN.md's "Boundaries" family: filled regions at 18% opacity. */
const REGION_OPACITY = 0.18;
/** Dots ≥ 8px diameter, with a 2px white ring — the same scatter mark spec every
 * family shares, applied here to the actual rows plotted over the grid. */
const POINT_RADIUS = 5;
const RING_WIDTH = 2;
/** Above this the boundary facets instead of one shared frame — DESIGN.md's
 * multiclass banding, shared with the "Class-conditional distributions" family. */
const SINGLE_FRAME_CLASS_CAP = 3;

/** Circle / triangle / square, in that order — the mandated non-colour channel so a
 * class is never identified by hue alone. Cycles past 3, though the caller never
 * asks for a 4th shape in the single-frame case (facets use one shape only). */
function Marker({
  shape,
  cx,
  cy,
  fill,
}: {
  shape: number;
  cx: number;
  cy: number;
  fill: string;
}) {
  const commonProps = { fill, fillOpacity: 0.85, stroke: '#ffffff', strokeWidth: RING_WIDTH };
  switch (shape % 3) {
    case 1: {
      // Triangle, centred on (cx, cy) with roughly the same visual weight as the circle.
      const r = POINT_RADIUS + 1.5;
      const points = [
        [cx, cy - r],
        [cx - r * 0.87, cy + r * 0.5],
        [cx + r * 0.87, cy + r * 0.5],
      ]
        .map((p) => p.join(','))
        .join(' ');
      return <polygon points={points} {...commonProps} />;
    }
    case 2: {
      const half = POINT_RADIUS;
      return <rect x={cx - half} y={cy - half} width={half * 2} height={half * 2} {...commonProps} />;
    }
    default:
      return <circle cx={cx} cy={cy} r={POINT_RADIUS} {...commonProps} />;
  }
}

function gridResolution(grid: BoundaryCell[]): number {
  return Math.round(Math.sqrt(grid.length)) || 1;
}

function domains(grid: BoundaryCell[]) {
  const xs = grid.map((c) => c.x);
  const ys = grid.map((c) => c.y);
  return {
    xMin: Math.min(...xs),
    xMax: Math.max(...xs),
    yMin: Math.min(...ys),
    yMax: Math.max(...ys),
  };
}

/** One frame, every class in its own hue and shape — DESIGN.md's ≤3-class case. */
function SingleFrameBoundary({ boundary }: { boundary: DecisionBoundary }) {
  const { xMin, xMax, yMin, yMax } = domains(boundary.grid);
  const x = scaleLinear().domain([xMin, xMax]).range([0, SIZE]);
  const y = scaleLinear().domain([yMin, yMax]).range([SIZE, 0]);
  const resolution = gridResolution(boundary.grid);
  const cellWidth = SIZE / resolution;

  const colourFor = (className: string) => {
    const index = boundary.classes.indexOf(className);
    return series[((index % 3) + 1) as 1 | 2 | 3].hex;
  };

  return (
    <svg
      role="img"
      aria-label={`Decision boundary over ${boundary.feature_x} and ${boundary.feature_y}, ${boundary.classes.length} classes.`}
      viewBox={`0 0 ${SIZE} ${SIZE}`}
      style={{ width: '100%', height: '100%' }}
    >
      <g>
        {boundary.grid.map((cell, i) => (
          <rect
            key={i}
            x={x(cell.x) - cellWidth / 2}
            y={y(cell.y) - cellWidth / 2}
            width={cellWidth + 0.5}
            height={cellWidth + 0.5}
            fill={colourFor(cell.predicted_class)}
            fillOpacity={REGION_OPACITY}
          />
        ))}
        {boundary.points.map((point, i) => (
          <Marker
            key={i}
            shape={boundary.classes.indexOf(point.actual_class)}
            cx={x(point.x)}
            cy={y(point.y)}
            fill={colourFor(point.actual_class)}
          />
        ))}
      </g>
      <rect x={0} y={0} width={SIZE} height={SIZE} fill="none" stroke={chart.axis.hex} strokeWidth={1} />
    </svg>
  );
}

/** One small binary panel per class (this class vs. everything else) — DESIGN.md's
 * 4-6 class case. Direct per-class colour slots stop being distinguishable past 3, so
 * each class gets its own single-hue frame instead of sharing one crowded one. */
function FacetedBoundary({ boundary }: { boundary: DecisionBoundary }) {
  const { xMin, xMax, yMin, yMax } = domains(boundary.grid);
  const facetSize = 150;
  const x = scaleLinear().domain([xMin, xMax]).range([0, facetSize]);
  const y = scaleLinear().domain([yMin, yMax]).range([facetSize, 0]);
  const resolution = gridResolution(boundary.grid);
  const cellWidth = facetSize / resolution;

  return (
    <Grid container spacing={1}>
      {boundary.classes.map((className) => (
        <Grid item xs={6} sm={4} key={className}>
          <Typography variant="caption" sx={{ display: 'block', mb: 0.5 }}>
            {className}
          </Typography>
          <svg
            role="img"
            aria-label={`${className} vs. the rest, over ${boundary.feature_x} and ${boundary.feature_y}.`}
            viewBox={`0 0 ${facetSize} ${facetSize}`}
            style={{ width: '100%', height: 'auto' }}
          >
            {boundary.grid.map((cell, i) => (
              <rect
                key={i}
                x={x(cell.x) - cellWidth / 2}
                y={y(cell.y) - cellWidth / 2}
                width={cellWidth + 0.5}
                height={cellWidth + 0.5}
                fill={cell.predicted_class === className ? series[1].hex : chart.gridline.hex}
                fillOpacity={cell.predicted_class === className ? REGION_OPACITY : 1}
              />
            ))}
            {boundary.points.map((point, i) => (
              <Marker
                key={i}
                shape={0}
                cx={x(point.x)}
                cy={y(point.y)}
                fill={point.actual_class === className ? series[1].hex : chart.inkMuted.hex}
              />
            ))}
            <rect
              x={0}
              y={0}
              width={facetSize}
              height={facetSize}
              fill="none"
              stroke={chart.axis.hex}
              strokeWidth={1}
            />
          </svg>
        </Grid>
      ))}
    </Grid>
  );
}

/**
 * FR-4.2's decision boundary for LDA/QDA (and, later, KNN/SVM): DESIGN.md's
 * "Boundaries" family. Renders nothing (a stated reason instead) when there aren't two
 * numeric columns to plot, or when there are more classes than the family supports at
 * all — both are facts about the data, not a broken chart.
 */
export function DecisionBoundaryChart({ boundary }: { boundary: DecisionBoundary }) {
  if (boundary.looks_continuous) {
    return (
      <Typography color="text.secondary">
        This column looks continuous — {boundary.classes.length} distinct values across not many
        more rows — rather than a genuine set of categories, so there's no boundary to draw.
        Try a regression method instead, or a target column with a small, fixed set of outcomes.
      </Typography>
    );
  }
  if (boundary.too_many_classes) {
    return (
      <Typography color="text.secondary">
        This has {boundary.classes.length} categories — too many to tell apart on one
        boundary plot, so there's nothing shown here.
      </Typography>
    );
  }
  if (boundary.grid.length === 0) {
    return (
      <Typography color="text.secondary">
        This dataset doesn't have two number columns to plot a boundary across.
      </Typography>
    );
  }
  if (boundary.classes.length <= SINGLE_FRAME_CLASS_CAP) {
    return <SingleFrameBoundary boundary={boundary} />;
  }
  return <FacetedBoundary boundary={boundary} />;
}

/** DESIGN.md is explicit this family has no meaningful table: a 2-D prediction raster
 * isn't tabular data. Ships the stated text summary instead — the two features
 * plotted, the class count, and each class's row count in the projection. */
export function boundarySummary(boundary: DecisionBoundary): string {
  if (boundary.looks_continuous) {
    return `This column looks continuous (${boundary.classes.length} distinct values) rather than a set of categories.`;
  }
  if (boundary.too_many_classes) {
    return `${boundary.classes.length} categories — too many for a boundary plot.`;
  }
  if (boundary.grid.length === 0) {
    return "This dataset doesn't have two number columns to plot a boundary across.";
  }
  const counts = boundary.classes.map((className) => {
    const n = boundary.points.filter((p) => p.actual_class === className).length;
    return `${className}: ${n}`;
  });
  return (
    `Plotted on ${boundary.feature_x} and ${boundary.feature_y}. ` +
    `${boundary.classes.length} classes — ${counts.join(', ')}.`
  );
}
