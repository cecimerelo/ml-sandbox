import Table from '@mui/material/Table';
import TableBody from '@mui/material/TableBody';
import TableCell from '@mui/material/TableCell';
import TableHead from '@mui/material/TableHead';
import TableRow from '@mui/material/TableRow';

/**
 * Bin/category × count — the table form DESIGN.md specifies for histograms, categorical
 * bars, and target distributions alike. One shape covers all three.
 */
export function DistributionTable({
  rows,
  columnLabel,
}: {
  rows: { label: string; count: number }[];
  columnLabel: string;
}) {
  return (
    <Table size="small">
      <TableHead>
        <TableRow>
          <TableCell>{columnLabel}</TableCell>
          <TableCell align="right">Count</TableCell>
        </TableRow>
      </TableHead>
      <TableBody>
        {rows.map((row) => (
          <TableRow key={row.label}>
            <TableCell>{row.label}</TableCell>
            <TableCell align="right">{row.count}</TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}
