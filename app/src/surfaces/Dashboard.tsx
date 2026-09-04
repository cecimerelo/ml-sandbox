import Alert from '@mui/material/Alert';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import { useState } from 'react';

import type { RecommendationRequest } from '../api/types';
import { ProblemForm } from '../form/ProblemForm';
import { RecommendationPanel } from '../panel/RecommendationPanel';
import type { Recommendation } from '../panel/types';
import { DatasetPanel } from '../detect/DatasetPanel';
import type { Detection } from '../detect/types';
import { Dropzone } from '../upload/Dropzone';
import type { DatasetSummary } from '../upload/Dropzone';
import { spacing } from '../theme/tokens';

/**
 * The Dashboard — the whole product loop: characterize, recommend, explain, explore,
 * compare.
 *
 * Block 1 is here. Block 2, the recommendation panel, arrives with 2.4 once 2.2 gives it
 * something to render; until then the submitted answers are shown so the form can be
 * exercised end to end.
 */
export function Dashboard() {
  const [result, setResult] = useState<Recommendation | null>(null);
  const [failed, setFailed] = useState<string | null>(null);
  const [dataset, setDataset] = useState<{ file: File; summary: DatasetSummary } | null>(null);
  const [detection, setDetection] = useState<Detection | null>(null);

  async function ask(request: RecommendationRequest) {
    setFailed(null);
    // Cleared before the request. Leaving the previous recommendation on screen while a
    // new one is computed shows an answer to a question the user has already changed.
    setResult(null);
    try {
      const response = await fetch('/api/recommend', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(request),
      });
      if (!response.ok) {
        setFailed('We could not work out a recommendation for that. Try again.');
        return;
      }
      setResult(await response.json());
    } catch {
      setFailed(
        "We couldn't reach the server, so nothing has been worked out yet. If you're " +
          'running this locally, check the API is up.',
      );
    }
  }

  return (
    // Centred in a reading column rather than filling the page. Text stays left-aligned
    // inside it: a centred paragraph gives every line a different starting point, and the
    // eye has to hunt for each one.
    <Box sx={{ maxWidth: spacing.readingMax, mx: 'auto' }}>
      {/* The heading and its one-line intro are centred; the questions below are not.
          A heading is a landmark and reads fine centred, but centring the explanations
          would give every line a different starting point, and the eye has to hunt for
          each one. */}
      <Typography variant="h4" component="h1" align="center" gutterBottom>
        Describe your problem
      </Typography>
      <Typography color="text.secondary" align="center" sx={{ mb: 5 }}>
        Answer what you can about your data and we will suggest a method, with the reasoning
        behind it. You do not need to upload anything.
      </Typography>

      {/* Above the form, because it is what decides the form's shape.

          Accepting a file does not change that shape yet — the questions still have to be
          answered by hand until detection lands. It is shown anyway so the control can be
          exercised, and that is a real cost worth naming: someone who uploads a file and
          then answers the same questions by hand has been given the impression the file
          was used. Detection is what closes it. */}
      <Dropzone
        onAccepted={(file, summary) => {
          setDataset({ file, summary });
          // A new file invalidates the old reading. Leaving it would fill the questions
          // with properties of a dataset nobody uploaded.
          setDetection(null);
        }}
        onCleared={() => {
          setDataset(null);
          setDetection(null);
        }}
      />

      {/* Choosing the outcome comes before anything else the file can say, because every
          other reading depends on it. The questions below still have to be answered by
          hand — carrying the detections into them is the shape switch, which is its own
          task. */}
      {dataset && (
        <DatasetPanel
          file={dataset.file}
          columns={dataset.summary.columns}
          unusable={dataset.summary.skipped}
          onDetected={setDetection}
        />
      )}

      <ProblemForm onSubmit={ask} detection={detection} />

      {failed && (
        <Alert severity="error" sx={{ mt: 4 }}>
          {failed}
        </Alert>
      )}

      {result && !failed && <RecommendationPanel result={result} />}
    </Box>
  );
}
