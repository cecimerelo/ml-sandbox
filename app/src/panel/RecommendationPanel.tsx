import Alert from '@mui/material/Alert';
import Box from '@mui/material/Box';
import Divider from '@mui/material/Divider';
import Paper from '@mui/material/Paper';
import Typography from '@mui/material/Typography';

import { PANEL } from '../copy/catalogue';
import { renderCopy } from '../copy/render';
import { spacing } from '../theme/tokens';
import { FitScore } from './FitScore';
import { indistinguishable } from './types';
import type { Recommendation, Suggestion, Support } from './types';

/**
 * Block 2 — the recommendation and the reasoning behind it.
 *
 * Every element renders from the rule layer, so nothing here needs a model to have been
 * trained on the user's data. It works with or without an uploaded dataset, which is the
 * whole of the advice-only product.
 */
export function RecommendationPanel({ result }: { result: Recommendation }) {
  const { recommended, alternatives, excluded, support, provisional } = result;
  const tied = alternatives.filter((a) => indistinguishable(recommended, a));

  return (
    <Paper variant="outlined" sx={{ p: 3, mt: `${spacing.sectionGap}px` }}>
      <Typography variant="overline" color="text.secondary">
        Suggested method
      </Typography>
      <Typography variant="h5" component="h2" gutterBottom>
        {recommended.label}
      </Typography>

      <Box sx={{ maxWidth: 260, mb: 3 }}>
        <FitScore shortfall={recommended.expected_shortfall} />
      </Box>

      {/* Said before the ranking is read, not after. Where the intervals overlap, the
          order between those methods is a coin toss, and presenting it as a ranking would
          be the confident wrong answer this whole layer exists to avoid. */}
      {tied.length > 0 && (
        <Alert severity="info" sx={{ mb: 3 }}>
          {tied.length === 1 ? 'One other method is' : `${tied.length} other methods are`} too
          close to call apart from this one — {tied.map((t) => t.label).join(', ')}. Any of
          them is a reasonable choice.
        </Alert>
      )}

      <Section heading={PANEL['panel.factors.heading']}>
        {/* The user's own answers, given back to them. The explanation is traceable to
            what they said, not to an authority — which is also why FR-2.3 forbids naming
            a source: there is no source to name, only their inputs and a rule. */}
        <Box component="ul" sx={{ pl: 3, m: 0 }}>
          {recommended.reasons.map((reason) => (
            <Typography component="li" key={reason} sx={{ mb: 0.5 }}>
              {renderCopy(reason)}
            </Typography>
          ))}
          {recommended.reasons.length === 0 && (
            <Typography component="li" color="text.secondary">
              Nothing about your problem pushed strongly in any direction, so this is the
              method that does best on data in general.
            </Typography>
          )}
        </Box>
      </Section>

      <Section heading={PANEL['panel.bias-variance.heading']}>
        <Typography>{renderCopy(PANEL['panel.bias-variance.explanation'])}</Typography>
      </Section>

      <Section heading={PANEL['panel.interpretability.heading']}>
        <Typography>{renderCopy(PANEL['panel.interpretability.explanation'])}</Typography>
      </Section>

      <Section heading="Other methods worth considering">
        {alternatives.map((s) => (
          <Alternative key={s.method} suggestion={s} />
        ))}
      </Section>

      {/* Returned rather than hidden. Withholding the best method leaves the user unable
          to see what their own constraint cost them. */}
      {excluded.length > 0 && (
        <Section heading="Ruled out by what you told us">
          <Typography color="text.secondary" sx={{ mb: 1 }}>
            You said you need to explain individual predictions, so these are not available
            — even where they would score better.
          </Typography>
          {excluded.slice(0, 3).map((s) => (
            <Alternative key={s.method} suggestion={s} />
          ))}
        </Section>
      )}

      <Divider sx={{ my: 2 }} />

      <Typography variant="body2" color="text.secondary">
        {evidence(support)}
      </Typography>
      {provisional && (
        <Typography variant="body2" color="text.secondary" sx={{ mt: 0.5 }}>
          This is built on an unfinished benchmark, so treat it as provisional.
        </Typography>
      )}
    </Paper>
  );
}

function Section({ heading, children }: { heading: string; children: React.ReactNode }) {
  return (
    <Box sx={{ mb: 3 }}>
      <Typography sx={{ fontWeight: 700, mb: 0.5 }}>{heading}</Typography>
      {children}
    </Box>
  );
}

function Alternative({ suggestion }: { suggestion: Suggestion }) {
  return (
    <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 1.5 }}>
      <Box sx={{ minWidth: 90 }}>
        <FitScore shortfall={suggestion.expected_shortfall} compact />
      </Box>
      <Typography>{suggestion.label}</Typography>
    </Box>
  );
}

/**
 * How much the study knows about a problem shaped like this one.
 *
 * Reported because the model's own uncertainty does not carry it: tree spread tracks how
 * hard a region is, not how unfamiliar, and that was measured rather than assumed.
 */
function evidence(support: Support): string {
  if (support.datasets === 0) {
    return (
      `No dataset in the study had ${support.field} = ${support.answer}, so this ` +
      'suggestion is worked out from neighbouring cases rather than measured on data like ' +
      'yours.'
    );
  }
  return (
    `Based on ${support.total} datasets, of which ${support.datasets} resembled yours on ` +
    `${support.field}.`
  );
}
