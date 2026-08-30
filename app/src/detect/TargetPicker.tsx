import Alert from '@mui/material/Alert';
import FormControl from '@mui/material/FormControl';
import InputLabel from '@mui/material/InputLabel';
import MenuItem from '@mui/material/MenuItem';
import Select from '@mui/material/Select';
import Typography from '@mui/material/Typography';

import { spacing } from '../theme/tokens';

/**
 * Which column is the outcome — the form's only sequential dependency.
 *
 * **Nothing below renders until this is answered**, because every detection depends on it.
 * That is also what makes the control safe: there is no default standing in for an answer
 * nobody gave.
 *
 * That last point is not a style choice. The study itself guessed at this — it took the
 * last column, on the belief that the source put the outcome there — and was wrong on five
 * of forty datasets, training models to predict the day of the month from a house's price.
 * It did not error; every method simply scored near zero, which reads as a hard dataset
 * (D-041). **A suggested default here would be that same guess with a human as its alibi.**
 */
export function TargetPicker({
  columns,
  value,
  error,
  onChange,
}: {
  columns: string[];
  value: string;
  error: string | null;
  onChange: (column: string) => void;
}) {
  return (
    <>
      <FormControl fullWidth sx={{ mb: `${spacing.fieldGap}px` }}>
        <InputLabel id="target-label">What are you trying to predict?</InputLabel>
        <Select
          labelId="target-label"
          label="What are you trying to predict?"
          value={value}
          onChange={(event) => onChange(event.target.value)}
          error={error !== null}
        >
          {columns.map((column) => (
            <MenuItem key={column} value={column}>
              {column}
            </MenuItem>
          ))}
        </Select>
        <Typography variant="body2" color="text.secondary" sx={{ mt: 0.5 }}>
          The column holding the answer you want the model to work out. Everything else
          becomes something it predicts from.
        </Typography>
      </FormControl>

      {error && (
        <Alert severity="error" sx={{ mb: `${spacing.fieldGap}px` }}>
          {error}
        </Alert>
      )}
    </>
  );
}
