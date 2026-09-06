import Button from '@mui/material/Button';
import Paper from '@mui/material/Paper';
import Typography from '@mui/material/Typography';

/**
 * The collapsed form, once a recommendation exists to scroll away from.
 *
 * **Not sticky** (D-052) — the top bar is the product's one sticky element. Scrolls away
 * with the rest of the page like everything else below it; `Edit` is reached by scrolling
 * back up, not by it following the reader down.
 *
 * Read-only; changing an answer means `Edit` first, which is also what keeps FR-1.7
 * intact here — nothing here can trigger a re-run.
 *
 * **Not the comma-joined answer dump the spine specifies.** Nine bare values with no
 * question beside them — "A number, Fewer than 500, Fewer than 10, Both, None..." — read
 * as noise, not as a summary; a value only means something next to the question it
 * answered, and there is no room for both in one line. A plain label plus `Edit` says
 * what's collapsed without pretending to summarise it.
 */
export function FormSummaryBar({ onEdit }: { onEdit: () => void }) {
  return (
    <Paper
      elevation={1}
      sx={{
        display: 'flex',
        alignItems: 'center',
        gap: 2,
        p: 1.5,
        borderRadius: 1,
        mb: 3,
      }}
    >
      <Typography variant="body2" color="text.secondary" sx={{ flex: 1 }}>
        Your answers
      </Typography>
      <Button size="small" onClick={onEdit}>
        Edit
      </Button>
    </Paper>
  );
}
