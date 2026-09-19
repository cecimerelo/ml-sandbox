import Table from '@mui/material/Table';
import TableBody from '@mui/material/TableBody';
import TableCell from '@mui/material/TableCell';
import TableHead from '@mui/material/TableHead';
import TableRow from '@mui/material/TableRow';
import Tooltip from '@mui/material/Tooltip';

import { chart, seq } from '../../theme/tokens';
import type { ConfusionMatrix } from './types';

/** Above this, DESIGN.md drops the in-cell numbers — an 11px count no longer fits a
 * cell smaller than the panel forces it to be past this point. */
const IN_CELL_NUMBERS_MAX = 10;

const CELL = 32;
const LABEL_WIDTH = 90;
const LABEL_HEIGHT = 60;

const SEQ_STEPS = [seq[100], seq[200], seq[300], seq[400], seq[500], seq[600], seq[700]];

/** One hue, light → dark on cell value — DESIGN.md's "Classification quality" family:
 * the sequential ramp, never the diverging one (a count has no sign to speak of). */
function colourFor(value: number, max: number): { fill: string; step: number } {
  if (max <= 0) return { fill: seq[100].hex, step: 0 };
  const t = value / max;
  const index = Math.min(SEQ_STEPS.length - 1, Math.floor(t * SEQ_STEPS.length));
  return { fill: SEQ_STEPS[index]!.hex, step: index };
}

/**
 * The confusion matrix: rows are the actual class, columns the predicted one.
 * DESIGN.md is explicit the matrix-as-table is the *better* representation here, not a
 * fallback for the chart — both render the same `labels`/`matrix` this component takes.
 */
export function ConfusionMatrixChart({ data }: { data: ConfusionMatrix }) {
  const n = data.labels.length;
  const showNumbers = n <= IN_CELL_NUMBERS_MAX;
  const max = Math.max(...data.matrix.flat(), 1);
  const width = LABEL_WIDTH + n * CELL;
  const height = LABEL_HEIGHT + n * CELL;

  return (
    <svg
      role="img"
      aria-label={`Confusion matrix over ${n} classes.`}
      viewBox={`0 0 ${width} ${height}`}
      style={{ width: '100%', height: 'auto' }}
    >
      {data.labels.map((label, i) => (
        <text
          key={`row-${label}`}
          x={LABEL_WIDTH - 8}
          y={LABEL_HEIGHT + i * CELL + CELL / 2}
          fontSize={11}
          fill={chart.ink.hex}
          textAnchor="end"
          dominantBaseline="middle"
        >
          {label.length > 12 ? `${label.slice(0, 11)}…` : label}
        </text>
      ))}
      {data.labels.map((label, j) => (
        <text
          key={`col-${label}`}
          x={LABEL_WIDTH + j * CELL + CELL / 2}
          y={LABEL_HEIGHT - 8}
          fontSize={11}
          fill={chart.ink.hex}
          textAnchor="start"
          transform={`rotate(-90, ${LABEL_WIDTH + j * CELL + CELL / 2}, ${LABEL_HEIGHT - 8})`}
        >
          {label.length > 12 ? `${label.slice(0, 11)}…` : label}
        </text>
      ))}
      <g>
        {data.matrix.map((row, i) =>
          row.map((value, j) => {
            const { fill, step } = colourFor(value, max);
            return (
              <Tooltip
                key={`${i}-${j}`}
                title={`Actual ${data.labels[i]}, predicted ${data.labels[j]}: ${value}`}
                disableInteractive
              >
                <g>
                  <rect
                    x={LABEL_WIDTH + j * CELL + 1}
                    y={LABEL_HEIGHT + i * CELL + 1}
                    width={CELL - 2}
                    height={CELL - 2}
                    fill={fill}
                  />
                  {showNumbers && (
                    <text
                      x={LABEL_WIDTH + j * CELL + CELL / 2}
                      y={LABEL_HEIGHT + i * CELL + CELL / 2}
                      fontSize={11}
                      textAnchor="middle"
                      dominantBaseline="middle"
                      fill={step >= 4 ? chart.surface.hex : chart.ink.hex}
                    >
                      {value}
                    </text>
                  )}
                </g>
              </Tooltip>
            );
          }),
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
  );
}

/** The matrix itself, as a real table with row/column headers — DESIGN.md's stated
 * table form for a confusion matrix, the better representation, not a fallback. */
export function ConfusionMatrixTable({ data }: { data: ConfusionMatrix }) {
  return (
    <Table size="small">
      <TableHead>
        <TableRow>
          <TableCell />
          {data.labels.map((label) => (
            <TableCell key={label} align="right">
              {label}
            </TableCell>
          ))}
        </TableRow>
      </TableHead>
      <TableBody>
        {data.labels.map((label, i) => (
          <TableRow key={label}>
            <TableCell component="th" scope="row">
              {label}
            </TableCell>
            {data.matrix[i]!.map((value, j) => (
              <TableCell key={data.labels[j]} align="right">
                {value}
              </TableCell>
            ))}
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}
