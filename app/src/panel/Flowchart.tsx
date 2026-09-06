import Accordion from '@mui/material/Accordion';
import AccordionDetails from '@mui/material/AccordionDetails';
import AccordionSummary from '@mui/material/AccordionSummary';
import Box from '@mui/material/Box';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import Typography from '@mui/material/Typography';

import { chart, series, spacing } from '../theme/tokens';
import type { Checkpoint } from './types';

/**
 * The method-selection flowchart — every question the engine checked, whether or not it
 * fired.
 *
 * **Built from `checkpoints`, not from `factors`.** The recommendation panel's "what led
 * to this" list only ever shows rules that favoured the recommended method — correct for
 * that purpose, but it means a user whose answers were entirely typical sees an empty list
 * with nothing to explain why. That is exactly the confusion this replaced: a single
 * fallback sentence with no way to tell "the engine ignored my answers" from "nothing
 * about them mattered". `checkpoints` is the full set of ten questions ISLR has an opinion
 * on, always present, so there is always something to check the recommendation against.
 *
 * **Fired and not-fired render differently, not just to different lists.** Fired
 * checkpoints form the connected path — the one this method actually took. Not-fired
 * checkpoints are named too, but plainly, as answers that were inside the range the
 * textbook has no rule for; they are not steps on a path, because nothing about them
 * moved the ranking.
 *
 * A rendered sequence of real DOM nodes, not an image: DESIGN.md requires the traversed
 * path be distinguishable, which a static picture cannot do.
 *
 * **One layout, not two.** DESIGN.md specifies a wide graph that collapses to a vertical
 * step list below 640px. There is no separate wide mode here: a linear path has nothing a
 * horizontal layout would show that a vertical one does not, so the "collapsed" form is
 * the only form.
 *
 * **No untaken branch is shown, and none is claimed.** DESIGN.md's flowchart is a binary
 * tree with both sides of every split visible. The engine does not compute the opposite
 * answer's effect — Layer 1 reports the rules that fired for the answer actually given,
 * not the counterfactual of a different one — so drawing that half would mean inventing
 * branches the engine never evaluated. A "checked, nothing applied" entry is not the same
 * claim as "here is what would have happened instead", and this is careful not to blur
 * the two.
 */
export function Flowchart({
  method,
  checkpoints,
}: {
  method: string;
  checkpoints: Checkpoint[];
}) {
  const fired = checkpoints.filter((c) => c.fired);
  const notFired = checkpoints.filter((c) => !c.fired);

  return (
    <Box>
      {fired.length > 0 ? (
        <Box component="ol" sx={{ listStyle: 'none', p: 0, m: 0 }}>
          {fired.map((checkpoint) => (
            <Step key={checkpoint.question} checkpoint={checkpoint} />
          ))}
          <TerminalNode method={method} />
        </Box>
      ) : (
        <Typography sx={{ mb: 2 }}>
          None of your answers pushed this choice in particular — {method} is simply the
          strongest performer on data in general, based on the benchmark.
        </Typography>
      )}

      {notFired.length > 0 && (
        <Accordion
          disableGutters
          elevation={0}
          square
          sx={{ mt: fired.length > 0 ? 2 : 0, '&:before': { display: 'none' } }}
        >
          <AccordionSummary expandIcon={<ExpandMoreIcon />} sx={{ px: 0 }}>
            <Typography variant="body2" color="text.secondary">
              What we discarded
            </Typography>
          </AccordionSummary>
          <AccordionDetails sx={{ px: 0 }}>
            <Box component="ul" sx={{ pl: 3, m: 0 }}>
              {notFired.map((checkpoint) => (
                <Typography
                  component="li"
                  key={checkpoint.question}
                  variant="body2"
                  color="text.secondary"
                  sx={{ mb: 0.5 }}
                >
                  <Box component="span" sx={{ fontStyle: 'italic' }}>
                    {checkpoint.question}
                  </Box>{' '}
                  ({checkpoint.answer}) — {checkpoint.claim}
                </Typography>
              ))}
            </Box>
          </AccordionDetails>
        </Accordion>
      )}
    </Box>
  );
}

function Step({ checkpoint }: { checkpoint: Checkpoint }) {
  return (
    <Box component="li" sx={{ display: 'flex', gap: 1.5 }}>
      <Rail last={false} />
      <Node>
        <Typography variant="body2" color="text.secondary">
          {checkpoint.question}
        </Typography>
        <Typography sx={{ fontWeight: 700 }}>{checkpoint.answer}</Typography>
        <Typography variant="body2" sx={{ mt: 0.5 }}>
          {checkpoint.claim}
        </Typography>
      </Node>
    </Box>
  );
}

function TerminalNode({ method }: { method: string }) {
  return (
    <Box component="li" sx={{ display: 'flex', gap: 1.5 }}>
      <Rail last />
      {/* The terminal (method) node takes a 2px border rather than the 1px every other
          node uses — the one non-colour carrier DESIGN.md asks for beyond the connecting
          line, so the destination is identifiable even without colour. */}
      <Node terminal>
        <Typography sx={{ fontWeight: 700 }}>{method}</Typography>
        <Typography variant="body2" color="text.secondary">
          recommended
        </Typography>
      </Node>
    </Box>
  );
}

/** The connecting line and step badge, to the left of each node. */
function Rail({ last }: { last: boolean }) {
  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', width: 24 }}>
      <Box
        sx={{
          width: 10,
          height: 10,
          borderRadius: '50%',
          bgcolor: series[1].hex,
          flexShrink: 0,
          mt: 1,
        }}
      />
      {!last && (
        <Box sx={{ width: 2, flexGrow: 1, bgcolor: series[1].hex, minHeight: 32 }} />
      )}
    </Box>
  );
}

function Node({
  terminal = false,
  children,
}: {
  terminal?: boolean;
  children: React.ReactNode;
}) {
  return (
    <Box
      sx={{
        flex: 1,
        mb: `${spacing.fieldGap}px`,
        p: 1.5,
        borderRadius: 1,
        border: terminal ? `2px solid ${series[1].hex}` : `1px solid ${chart.gridline.hex}`,
        bgcolor: terminal ? '#f5f9ff' : 'background.paper',
      }}
    >
      {children}
    </Box>
  );
}
