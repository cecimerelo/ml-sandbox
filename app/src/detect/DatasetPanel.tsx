import CircularProgress from '@mui/material/CircularProgress';
import Box from '@mui/material/Box';
import { useState } from 'react';

import type { Task } from '../api/types';
import type { ClassBalanceAnswer } from '../form/options';
import { DetectedFields } from './DetectedFields';
import { TargetPicker } from './TargetPicker';
import type { Detection } from './types';

interface Answers {
  task: Task;
  feature_types: string;
  missing: string;
  class_balance: ClassBalanceAnswer | '';
}

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
  onDetected,
}: {
  file: File;
  columns: string[];
  onDetected: (detection: Detection, answers: Answers) => void;
}) {
  const [target, setTarget] = useState('');
  const [detection, setDetection] = useState<Detection | null>(null);
  const [answers, setAnswers] = useState<Answers | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function choose(column: string) {
    setTarget(column);
    setError(null);
    // Cleared before the request, not after it. Leaving the previous reading on screen
    // while a new target is resolving shows properties of a question nobody asked.
    setDetection(null);
    setAnswers(null);
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

      const next: Answers = {
        task: payload.task,
        feature_types: payload.feature_types,
        missing: payload.missing,
        class_balance: payload.class_balance === 'not applicable' ? '' : payload.class_balance,
      };
      setDetection(payload);
      setAnswers(next);
      onDetected(payload, next);
    } catch {
      setError("We couldn't reach the server, so nothing has been read from your file yet.");
    } finally {
      setBusy(false);
    }
  }

  function change(field: string, value: string) {
    setAnswers((current) => {
      if (!current) return current;
      const next = { ...current, [field]: value } as Answers;
      if (detection) onDetected(detection, next);
      return next;
    });
  }

  return (
    <Box>
      <TargetPicker columns={columns} value={target} error={error} onChange={choose} />

      {busy && (
        <Box sx={{ display: 'flex', justifyContent: 'center', py: 2 }}>
          <CircularProgress size={24} aria-label="Reading your file" />
        </Box>
      )}

      {/* Nothing below the target renders until it is chosen and resolved — the form's
          only sequential dependency, and the reason there is no default above. */}
      {detection && answers && (
        <DetectedFields detection={detection} answers={answers} onChange={change} />
      )}
    </Box>
  );
}
