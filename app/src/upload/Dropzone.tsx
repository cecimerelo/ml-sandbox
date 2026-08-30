import Alert from '@mui/material/Alert';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Tooltip from '@mui/material/Tooltip';
import Typography from '@mui/material/Typography';
import { useRef, useState } from 'react';

import { MAX_BYTES, tooLargeMessage } from './limits';

export interface DatasetSummary {
  columns: string[];
  rows: number;
  skipped: string[];
}

/**
 * Uploading a dataset, and every way that can go wrong.
 *
 * **Rejection never changes the page.** The dropzone stays open, the form keeps its shape,
 * and prior answers are untouched — someone who dropped the wrong file has not withdrawn
 * anything they already said, and making them re-answer would be a punishment for a
 * mis-click.
 *
 * **Size is checked before the upload begins**, so an oversized file never crosses the
 * wire. Every other refusal is the server's, which keeps each limit beside the sentence
 * that explains it.
 */
export function Dropzone({
  onAccepted,
}: {
  onAccepted: (file: File, summary: DatasetSummary) => void;
}) {
  const [error, setError] = useState<string | null>(null);
  const [summary, setSummary] = useState<DatasetSummary | null>(null);
  const [busy, setBusy] = useState(false);
  const input = useRef<HTMLInputElement>(null);

  async function handle(file: File) {
    setError(null);

    if (file.size > MAX_BYTES) {
      setError(tooLargeMessage(file.size));
      return;
    }

    setBusy(true);
    try {
      const body = new FormData();
      body.append('file', file);
      const response = await fetch('/api/dataset', { method: 'POST', body });
      const payload = await response.json();

      if (!response.ok) {
        setError(payload?.detail?.message ?? 'Something went wrong reading that file.');
        return;
      }
      setSummary(payload);
      onAccepted(file, payload);
    } catch {
      setError("We couldn't read that file. Try again.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <Box sx={{ mb: 4 }}>
      <Box
        sx={{
          border: '1px dashed',
          borderColor: 'divider',
          borderRadius: 1,
          p: 3,
          textAlign: 'center',
        }}
        onDragOver={(event) => event.preventDefault()}
        onDrop={(event) => {
          event.preventDefault();
          const file = event.dataTransfer.files[0];
          if (file) void handle(file);
        }}
      >
        <Typography gutterBottom>Have a dataset? Drop a CSV here.</Typography>
        <Button variant="outlined" onClick={() => input.current?.click()} disabled={busy}>
          {busy ? 'Reading…' : 'Choose a file'}
        </Button>
        <input
          ref={input}
          type="file"
          accept=".csv,text/csv"
          hidden
          aria-label="Upload a CSV"
          onChange={(event) => {
            const file = event.target.files?.[0];
            if (file) void handle(file);
            // Cleared so choosing the same file twice still fires a change.
            event.target.value = '';
          }}
        />
        <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
          Or answer the questions below without one.
        </Typography>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mt: 2 }}>
          {error}
        </Alert>
      )}

      {summary && !error && (
        <Alert severity="success" sx={{ mt: 2 }}>
          {summary.rows.toLocaleString()} rows, {summary.columns.length} usable columns.
          {summary.skipped.length > 0 && (
            <>
              {' '}
              {/* Named on hover rather than listed: a user with forty skipped columns needs
                  to know it happened, not to read forty names. But they must be able to. */}
              <Tooltip title={summary.skipped.join(', ')}>
                <Box component="span" sx={{ borderBottom: '1px dotted', cursor: 'help' }}>
                  {summary.skipped.length} column{summary.skipped.length === 1 ? '' : 's'} skipped
                </Box>
              </Tooltip>{' '}
              — dates and free text aren&apos;t supported yet.
            </>
          )}
        </Alert>
      )}
    </Box>
  );
}
