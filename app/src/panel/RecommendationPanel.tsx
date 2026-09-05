import Box from '@mui/material/Box';
import Chip from '@mui/material/Chip';
import Divider from '@mui/material/Divider';
import Paper from '@mui/material/Paper';
import Typography from '@mui/material/Typography';

import { PANEL } from '../copy/catalogue';
import { renderCopy } from '../copy/render';
import { spacing } from '../theme/tokens';
import { FitScore } from './FitScore';
import { indistinguishable } from './types';
import type { Position as PositionType, Recommendation, Suggestion, Support } from './types';

/**
 * Block 2 — the recommendation and the reasoning behind it.
 *
 * Every element renders from the rule layer, so nothing here needs a model to have been
 * trained on the user's data. It works with or without an uploaded dataset, which is the
 * whole of the advice-only product.
 */
export function RecommendationPanel({ result }: { result: Recommendation }) {
  const { recommended, alternatives, excluded, support, provisional } = result;
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

      <Section heading={PANEL['panel.factors.heading']}>
        {/* The user's own answers first — traceable to what they said, not to an
            authority, which is also why FR-2.3 forbids naming a source. The method's
            fixed properties (flexibility, interpretability) close the list: they hold
            whatever the user answered, so they read as consequences of the recommendation
            rather than reasons for it. One list, one place to look, instead of three
            sections making the same kind of claim in three different shapes. */}
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
          <li>
            <Position method="The chosen method" position={recommended.flexibility} />
          </li>
          <li>
            <Position method="The chosen method" position={recommended.interpretability} />
          </li>
        </Box>
      </Section>

      {/* The tie is marked on the method it applies to, not announced separately above.
          A banner listing the same names the list repeats underneath gives a reader two
          places to look and makes the more important half — that these are equivalent —
          read as a footnote to the less important half. */}
      <Section heading="Other methods worth considering">
        {alternatives.map((s) => (
          <Alternative
            key={s.method}
            suggestion={s}
            tiedWith={indistinguishable(recommended, s) ? recommended.label : null}
          />
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

      {/* The disclaimer this whole panel needs: nothing here has been trained on the
          user's own data. Until Epic 4 fits the recommended method on an uploaded
          dataset, every number is from the benchmark alone, and a reader could otherwise
          take "based on 106 datasets" to mean their file was one of them. */}
      <Typography variant="body2" color="text.secondary">
        This suggestion is based only on your answers to the form — nothing here has been
        trained or tested on your own data.
      </Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mt: 0.5 }}>
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

/**
 * One line: the method's position, then what it means for this method.
 *
 * The name identifies whose position this is and is italicised for it; the label
 * ("flexible", "opaque") is a plain word the sentence already carries and does not need
 * weight of its own.
 */
function Position({ method, position }: { method: string; position: PositionType }) {
  return (
    <Typography component="span">
      <Box component="span" sx={{ fontStyle: 'italic' }}>
        {method}
      </Box>{' '}
      is {position.label} — {position.detail}
    </Typography>
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

function Alternative({
  suggestion,
  tiedWith = null,
}: {
  suggestion: Suggestion;
  /** The recommended method this one cannot be told apart from, if that is the case. */
  tiedWith?: string | null;
}) {
  return (
    <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 1.5 }}>
      <Box sx={{ minWidth: 90 }}>
        <FitScore shortfall={suggestion.expected_shortfall} compact />
      </Box>
      <Typography>{suggestion.label}</Typography>
      {tiedWith && (
        // A mark, not a sentence: the spec requires that an overlapping ranking not be
        // shown as a finding, but the earlier full sentence was heavier than the signal
        // needed. `title` carries the reason for anyone who wants it, without spending a
        // line of body text on every tied method.
        <Chip
          label="≈ tied"
          size="small"
          variant="outlined"
          title={`Too close to call apart from ${tiedWith} — the model does not distinguish them.`}
        />
      )}
    </Box>
  );
}

/**
 * How much the study knows about a problem shaped like this one.
 *
 * Reported because the model's own uncertainty does not carry it: tree spread tracks how
 * hard a region is, not how unfamiliar, and that was measured rather than assumed.
 */
/** The engine's internal field names, in the words the form actually used to ask. */
const FIELD_LABEL: Record<string, string> = {
  task: 'what you are predicting',
  rows: 'how many rows',
  features: 'how many columns',
  feature_types: 'what kind of columns',
  missing: 'how much is missing',
  class_balance: 'category sizes',
};

function evidence(support: Support): string {
  const field = FIELD_LABEL[support.field] ?? support.field;
  if (support.datasets === 0) {
    return (
      `No dataset in the study had an answer like yours for ${field}, so this ` +
      'suggestion is worked out from neighbouring cases rather than measured on data like ' +
      'yours.'
    );
  }
  return (
    `Based on ${support.total} datasets, of which ${support.datasets} resembled yours on ` +
    `${field}.`
  );
}
