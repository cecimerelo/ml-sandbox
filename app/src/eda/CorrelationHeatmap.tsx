import Paper from '@mui/material/Paper';
import Table from '@mui/material/Table';
import TableBody from '@mui/material/TableBody';
import TableCell from '@mui/material/TableCell';
import TableHead from '@mui/material/TableHead';
import TableRow from '@mui/material/TableRow';
import Tooltip from '@mui/material/Tooltip';
import Typography from '@mui/material/Typography';

import { chart, diverging } from '../theme/tokens';
import { PlotPanel } from './PlotPanel';
import type { CorrelationMatrix } from './types';

const MAX_CORRELATION_FEATURES = 30;
/** Above this, an 11px `r` value no longer fits the cell (DESIGN.md's stated floor). */
const IN_CELL_NUMBERS_MAX = 20;

const CELL = 28;
const LABEL_WIDTH = 90;
const LABEL_HEIGHT = 60;

function hexToRgb(hex: string): [number, number, number] {
  const n = Number.parseInt(hex.slice(1), 16);
  return [(n >> 16) & 255, (n >> 8) & 255, n & 255];
}

function mix(a: string, b: string, t: number): string {
  const [ar, ag, ab] = hexToRgb(a);
  const [br, bg, bb] = hexToRgb(b);
  const round = (x: number) => Math.round(x);
  return `rgb(${round(ar + (br - ar) * t)}, ${round(ag + (bg - ag) * t)}, ${round(ab + (bb - ab) * t)})`;
}

/** Blue ↔ red through a neutral gray midpoint. `r` runs −1..+1; zero must read as
 * "nothing", which the diverging ramp is the one legitimate use of (DESIGN.md). */
function colourFor(r: number): string {
  if (r >= 0) return mix(diverging.mid.hex, diverging.pos700.hex, Math.min(r, 1));
  return mix(diverging.mid.hex, diverging.neg700.hex, Math.min(-r, 1));
}

/**
 * Pairwise correlation among the highest-variance numeric features — the one true
 * diverging case in this product's chart palette (DESIGN.md § Correlation heatmap).
 *
 * Degenerate cases render their own stated panel rather than an empty grid: fewer than
 * two numeric features (which includes an all-categorical file) means there is nothing
 * to correlate, and that is a fact about the data, not an error — so it renders outside
 * `PlotPanel` entirely rather than offering a "View as table" toggle for a table that
 * cannot exist.
 */
export function CorrelationHeatmap({ data }: { data: CorrelationMatrix }) {
  if (data.features.length < 2) {
    return (
      <Paper variant="outlined" sx={{ p: 3 }}>
        <Typography sx={{ fontWeight: 700, mb: 1 }}>Correlation</Typography>
        <Typography color="text.secondary">
          {data.total_numeric === 0
            ? 'None of your columns are numbers, so there is nothing to correlate.'
            : 'Fewer than two numeric columns, so there is nothing to correlate.'}
        </Typography>
      </Paper>
    );
  }

  const n = data.features.length;
  const showNumbers = n <= IN_CELL_NUMBERS_MAX;
  const truncated = n < data.total_numeric;
  const width = LABEL_WIDTH + n * CELL;
  const height = LABEL_HEIGHT + n * CELL;

  const subtitle = truncated
    ? `Showing the ${MAX_CORRELATION_FEATURES} features with the most variation, of ${data.total_numeric}.`
    : undefined;

  return (
    <PlotPanel
      title="Correlation"
      {...(subtitle ? { subtitle } : {})}
      aspect="auto"
      chart={
        <svg
          role="img"
          aria-label={`Correlation heatmap of ${n} features.`}
          viewBox={`0 0 ${width} ${height}`}
          style={{ width: '100%', height: 'auto' }}
        >
          {data.features.map((rowFeature, i) => (
            <text
              key={`row-${rowFeature}`}
              x={LABEL_WIDTH - 8}
              y={LABEL_HEIGHT + i * CELL + CELL / 2}
              fontSize={11}
              fill={chart.ink.hex}
              textAnchor="end"
              dominantBaseline="middle"
            >
              {rowFeature.length > 12 ? `${rowFeature.slice(0, 11)}…` : rowFeature}
            </text>
          ))}
          {data.features.map((colFeature, j) => (
            <text
              key={`col-${colFeature}`}
              x={LABEL_WIDTH + j * CELL + CELL / 2}
              y={LABEL_HEIGHT - 8}
              fontSize={11}
              fill={chart.ink.hex}
              textAnchor="start"
              transform={`rotate(-90, ${LABEL_WIDTH + j * CELL + CELL / 2}, ${LABEL_HEIGHT - 8})`}
            >
              {colFeature.length > 12 ? `${colFeature.slice(0, 11)}…` : colFeature}
            </text>
          ))}
          <g>
            {data.values.map((row, i) =>
              row.map((r, j) => (
                <Tooltip
                  key={`${i}-${j}`}
                  title={`${data.features[i]} × ${data.features[j]}: r = ${r.toFixed(2)}`}
                  disableInteractive
                >
                  <g>
                    <rect
                      x={LABEL_WIDTH + j * CELL + 1}
                      y={LABEL_HEIGHT + i * CELL + 1}
                      width={CELL - 2}
                      height={CELL - 2}
                      fill={colourFor(r)}
                    />
                    {showNumbers && (
                      <text
                        x={LABEL_WIDTH + j * CELL + CELL / 2}
                        y={LABEL_HEIGHT + i * CELL + CELL / 2}
                        fontSize={10}
                        textAnchor="middle"
                        dominantBaseline="middle"
                        fill={Math.abs(r) > 0.6 ? chart.surface.hex : chart.ink.hex}
                      >
                        {r.toFixed(1)}
                      </text>
                    )}
                  </g>
                </Tooltip>
              )),
            )}
          </g>
          <rect
            x={LABEL_WIDTH}
            y={LABEL_HEIGHT}
            width={n * CELL}
            height={n * CELL}
            fill="none"
            stroke={chart.axis.hex}
            strokeWidth={1}
          />
        </svg>
      }
      table={<CorrelationTable data={data} />}
    />
  );
}

/** The matrix itself, as a real table with row and column headers — DESIGN.md is
 * explicit this is the *better* representation for a correlation heatmap, not a
 * fallback for the chart. */
function CorrelationTable({ data }: { data: CorrelationMatrix }) {
  return (
    <Table size="small">
      <TableHead>
        <TableRow>
          <TableCell />
          {data.features.map((f) => (
            <TableCell key={f} align="right">
              {f}
            </TableCell>
          ))}
        </TableRow>
      </TableHead>
      <TableBody>
        {data.features.map((rowFeature, i) => (
          <TableRow key={rowFeature}>
            <TableCell component="th" scope="row">
              {rowFeature}
            </TableCell>
            {data.values[i]!.map((r, j) => (
              <TableCell key={data.features[j]} align="right">
                {r.toFixed(2)}
              </TableCell>
            ))}
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}
