import Table from '@mui/material/Table';
import TableBody from '@mui/material/TableBody';
import TableCell from '@mui/material/TableCell';
import TableContainer from '@mui/material/TableContainer';
import TableHead from '@mui/material/TableHead';
import TableRow from '@mui/material/TableRow';
import Typography from '@mui/material/Typography';

import { PANEL } from '../copy/catalogue';
import { chrome } from '../theme/tokens';
import type { Axis, Suggestion } from './types';

/**
 * The method characteristics table — advice-only mode's only evidence artifact.
 *
 * With no dataset uploaded there is nothing to fit and nothing to plot, so this table is
 * the sole thing a user can use to judge the recommendation against its alternatives with
 * their own eyes. Renders from the rule layer and the benchmark aggregate alone; it never
 * touches the user's data (FR-2.2).
 *
 * Two of the five columns are computed from the benchmark rather than declared from
 * theory (D-049) — accuracy potential and training speed have no theoretical property to
 * read from the registry, and writing one by hand risked the table contradicting a
 * measurement the study actually made.
 */
export function CharacteristicsTable({
  recommended,
  alternatives,
}: {
  recommended: Suggestion;
  alternatives: Suggestion[];
}) {
  const rows = [recommended, ...alternatives].filter((s) => s.characteristics !== null);
  if (rows.length === 0) return null;

  return (
    // Scrolls its own width rather than the panel's. Five word-plus-dots columns do not
    // fit a narrow panel at a readable size, and the panel itself must not grow to fit
    // them — a table is the one thing here allowed to need its own scrollbar.
    <TableContainer sx={{ maxWidth: '100%' }}>
      <Table size="small" sx={{ minWidth: 560 }}>
        <TableHead>
          <TableRow>
            <TableCell>{PANEL['panel.characteristics.column.method']}</TableCell>
            <TableCell>{PANEL['panel.characteristics.column.interpretability']}</TableCell>
            <TableCell>{PANEL['panel.characteristics.column.non-linearity']}</TableCell>
            <TableCell>{PANEL['panel.characteristics.column.missing-values']}</TableCell>
            <TableCell>{PANEL['panel.characteristics.column.accuracy']}</TableCell>
            <TableCell>{PANEL['panel.characteristics.column.speed']}</TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {rows.map((row) => {
            const c = row.characteristics!;
            const isRecommended = row.method === recommended.method;
            return (
              <TableRow
                key={row.method}
                {...(isRecommended
                  ? {
                      sx: {
                        bgcolor: chrome.detected.hex + '14',
                        borderLeft: `2px solid ${chrome.detected.hex}`,
                      },
                    }
                  : {})}
              >
                <TableCell>{row.label}</TableCell>
                <AxisCell axis={c.interpretability} />
                <AxisCell axis={c.handles_non_linearity} />
                <AxisCell axis={c.handles_missing_values} />
                <AxisCell axis={c.accuracy_potential} />
                <AxisCell axis={c.training_speed} />
              </TableRow>
            );
          })}
        </TableBody>
      </Table>
    </TableContainer>
  );
}

/**
 * Two carriers, both always present: a word and a three-dot rating. Neither the status
 * palette nor colour alone — DESIGN.md is explicit this is an ordinal rating, not a
 * red/amber/green judgement, so the dots differ only in fill, never in hue.
 */
function AxisCell({ axis }: { axis: Axis }) {
  return (
    <TableCell>
      <Typography variant="body2" component="span">
        {axis.word}
      </Typography>
      <Typography
        component="span"
        aria-hidden
        sx={{ ml: 0.75, letterSpacing: 1, color: 'text.secondary' }}
      >
        {'●'.repeat(axis.step)}
        {'○'.repeat(3 - axis.step)}
      </Typography>
    </TableCell>
  );
}
