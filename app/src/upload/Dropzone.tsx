import CheckCircleOutlineIcon from '@mui/icons-material/CheckCircleOutline';
import UploadFileIcon from '@mui/icons-material/UploadFile';
import Alert from '@mui/material/Alert';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import Tooltip from '@mui/material/Tooltip';
import Typography from '@mui/material/Typography';
import { useRef, useState } from 'react';

import { MAX_BYTES, tooLargeMessage } from './limits';

/**
 * Distinct from every message about the file itself.
 *
 * Saying "we couldn't read that file" when the server was unreachable sends someone to
 * inspect a file that is perfectly fine — which is exactly what happened the first time
 * this control was used against a stale dev server. The two failures look identical from
 * inside the `catch`, so they are told apart before reaching it.
 */
/**
 * Dropping several files at once is easy to do by accident and easy to handle wrongly.
 *
 * Taking the first and ignoring the rest is the tempting version, and it is silent: the
 * user sees one file accepted and has no way to know which one, or that the others were
 * discarded. Refusing and saying so costs them one more drag and tells them the truth.
 */
const ONE_AT_A_TIME =
  'Drop one file at a time — we can only work with a single dataset.';

const UNREACHABLE =
  "We couldn't reach the server, so we haven't looked at your file yet. If you're running " +
  'this locally, check the API is up.';

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
  const [name, setName] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const input = useRef<HTMLInputElement>(null);
  const accepted = summary !== null && error === null;

  function handleDropped(files: FileList | null) {
    if (!files || files.length === 0) return;
    if (files.length > 1) {
      setError(ONE_AT_A_TIME);
      setName(null);
      setSummary(null);
      return;
    }
    void handle(files[0]!);
  }

  async function handle(file: File) {
    setError(null);
    // Dropped as soon as another file is tried. Leaving the previous name on screen while
    // a new one is being read says the wrong file was accepted.
    setName(null);
    setSummary(null);

    if (file.size > MAX_BYTES) {
      setError(tooLargeMessage(file.size));
      return;
    }

    setBusy(true);
    try {
      const body = new FormData();
      body.append('file', file);
      const response = await fetch('/api/dataset', { method: 'POST', body });

      let payload: { detail?: { message?: string } } | DatasetSummary | null = null;
      try {
        payload = await response.json();
      } catch {
        // A response that is not JSON is not this endpoint answering. In development it is
        // usually the dev server's HTML fallback, which means the API is unreachable and
        // the file is blameless.
        setError(UNREACHABLE);
        return;
      }

      if (!response.ok) {
        const message = (payload as { detail?: { message?: string } })?.detail?.message;
        // A refusal without our message is not our refusal — say so rather than inventing
        // a reason the file might have been rejected for.
        setError(message ?? UNREACHABLE);
        return;
      }
      setSummary(payload as DatasetSummary);
      setName(file.name);
      onAccepted(file, payload as DatasetSummary);
    } catch {
      // fetch only rejects when the request never completed.
      setError(UNREACHABLE);
    } finally {
      setBusy(false);
    }
  }

  return (
    <Box sx={{ mb: 4 }}>
      <Box
        sx={{
          border: '1px dashed',
          // The border answers too, so the state is not carried by the icon alone.
          borderColor: accepted ? 'success.main' : 'divider',
          borderRadius: 1,
          p: 3,
          textAlign: 'center',
        }}
        onDragOver={(event) => event.preventDefault()}
        onDrop={(event) => {
          event.preventDefault();
          handleDropped(event.dataTransfer.files);
        }}
      >
        {/* The zone itself changes, not only the message beneath it. Left unchanged, a
            control that has just taken someone's file still reads as empty, and the only
            confirmation is a sentence somewhere below — which is easy to miss and easy to
            mistake for being about a previous attempt. */}
        {accepted ? (
          <>
            <CheckCircleOutlineIcon color="success" fontSize="large" />
            <Typography gutterBottom sx={{ mt: 1 }}>
              {/* The icon carries the same meaning as the word, so a reader who cannot see
                  colour or the glyph still gets it. */}
              <Box component="span" sx={{ fontWeight: 700 }}>
                {name}
              </Box>{' '}
              loaded.
            </Typography>
            <Button variant="outlined" onClick={() => input.current?.click()} disabled={busy}>
              {busy ? 'Reading…' : 'Choose a different file'}
            </Button>
          </>
        ) : (
          <>
            <UploadFileIcon color="action" fontSize="large" />
            <Typography gutterBottom sx={{ mt: 1 }}>
              Have a dataset? Drop a CSV here.
            </Typography>
            <Button variant="outlined" onClick={() => input.current?.click()} disabled={busy}>
              {busy ? 'Reading…' : 'Choose a file'}
            </Button>
          </>
        )}
        <input
          ref={input}
          type="file"
          accept=".csv,text/csv"
          hidden
          aria-label="Upload a CSV"
          onChange={(event) => {
            handleDropped(event.target.files);
            // Cleared so choosing the same file twice still fires a change.
            event.target.value = '';
          }}
        />
        {!accepted && (
          <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
            Or answer the questions below without one.
          </Typography>
        )}
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
