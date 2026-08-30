import Alert from '@mui/material/Alert';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import { useState } from 'react';

import type { RecommendationRequest } from '../api/types';
import { ProblemForm } from '../form/ProblemForm';
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
  const [submitted, setSubmitted] = useState<RecommendationRequest | null>(null);

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

      <ProblemForm onSubmit={setSubmitted} />

      {submitted && (
        <Alert severity="info" sx={{ mt: 4 }}>
          Ready to send. The recommendation panel arrives with 2.4.
          <pre style={{ margin: 0, overflowX: 'auto' }}>
            {JSON.stringify(submitted, null, 2)}
          </pre>
        </Alert>
      )}
    </Box>
  );
}
