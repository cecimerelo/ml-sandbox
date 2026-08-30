import CircularProgress from '@mui/material/CircularProgress';
import Box from '@mui/material/Box';
import { useState } from 'react';

import type { SkippedColumn } from '../upload/Dropzone';
import { TargetPicker } from './TargetPicker';
import type { Detection } from './types';

/**
 * The uploaded-dataset path: pick the outcome, then confirm what the file said.
 *
 * The file is sent again with the detection request rather than held on the server between
 * calls. The browser keeps the only copy, and the server has it for the length of one
 * request — which is what FR-7.2 promises and what the privacy notice will have to be true
 * about.
 */
export function DatasetPanel({
  file,
  columns,
  unusable,
  onDetected,
}: {
  file: File;
  columns: string[];
  unusable: SkippedColumn[];
  onDetected: (detection: Detection | null) => void;
}) {
  const [target, setTarget] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function choose(column: string) {
    setTarget(column);
    setError(null);
    // Cleared before the request, not after it. Leaving the previous reading in the form
    // while a new target resolves shows properties of a question nobody asked.
    onDetected(null);
    setBusy(true);

    try {
      const body = new FormData();
      body.append('file', file);
      body.append('target', column);
      const response = await fetch('/api/dataset/detect', { method: 'POST', body });
      const payload = await response.json();

      if (!response.ok) {
        // A target that cannot be predicted is not a failure of the file. The message
        // names the column and the user fixes it by picking another.
        setError(payload?.detail?.message ?? 'We could not read that column.');
        return;
      }

      onDetected(payload);
    } catch {
      setError("We couldn't reach the server, so nothing has been read from your file yet.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <Box>
      <TargetPicker
        columns={columns}
        unusable={unusable}
        value={target}
        error={error}
        onChange={choose}
      />

      {busy && (
        <Box sx={{ display: 'flex', justifyContent: 'center', py: 2 }}>
          <CircularProgress size={24} aria-label="Reading your file" />
        </Box>
      )}

      {/* Nothing is rendered for the readings themselves. They fill the questions that
          already exist below — a second block showing the same six answers put two
          controls for each on the page and left the user to work out which one counted. */}
    </Box>
  );
}
