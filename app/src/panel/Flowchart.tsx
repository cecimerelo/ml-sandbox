import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import Chip from '@mui/material/Chip';

import { chart, series, spacing } from '../theme/tokens';
import type { DecisionFactor } from './types';

/**
 * The method-selection flowchart — the path the engine actually took.
 *
 * **Built from `factors`, not drawn separately from them.** DESIGN.md specifies a binary
 * decision tree with both the traversed path and the untaken branch shown at every split.
 * The engine does not compute the untaken side: Layer 1 reports the rules that fired in
 * the user's favour, not the counterfactual of what would have fired on the opposite
 * answer. Rendering that half would mean inventing branches the engine never evaluated —
 * a diagram that looks more complete than the reasoning behind it.
 *
 * So this renders the **traversed path only**: one step per factor, in the order returned,
 * ending in the recommended method as a terminal node. It is still "inspectable rather
 * than asserted" (the issue's own words) — every step names a real answer and a real rule —
 * it is just a path rather than a tree. Recorded as a scope decision, not a silent gap.
 *
 * A rendered sequence of real DOM nodes, not an image: DESIGN.md requires the traversed
 * path be distinguishable, which a static picture cannot do, and it rules out a plot
 * family's axes or aspect ratio here — there are none.
 *
 * **One layout, not two.** DESIGN.md specifies a wide graph that collapses to a vertical
 * step list below 640px. There is no separate wide mode here: a linear path has nothing a
 * horizontal layout would show that a vertical one does not, so the "collapsed" form is
 * the only form. If branch data is ever added, a wide graph becomes worth building and
 * this component is where it would replace the current one, not extend it.
 */
export function Flowchart({ method, factors }: { method: string; factors: DecisionFactor[] }) {
  if (factors.length === 0) {
    return (
      <Typography color="text.secondary">
        Nothing about your answers pushed this choice in particular — {method} is simply
        the strongest performer on data in general.
      </Typography>
    );
  }

  return (
    <Box component="ol" sx={{ listStyle: 'none', p: 0, m: 0 }}>
      {factors.map((factor, index) => (
        <Step key={`${factor.question}-${factor.answer}`} number={index + 1} factor={factor} />
      ))}
      <TerminalNode number={factors.length + 1} method={method} />
    </Box>
  );
}

function Step({ number, factor }: { number: number; factor: DecisionFactor }) {
  return (
    <Box component="li" sx={{ display: 'flex', gap: 1.5 }}>
      <Rail last={false} />
      <Node number={number}>
        <Typography variant="body2" color="text.secondary">
          {factor.question}
        </Typography>
        <Typography sx={{ fontWeight: 700 }}>{factor.answer}</Typography>
        <Typography variant="body2" sx={{ mt: 0.5 }}>
          {factor.claim}
        </Typography>
        {factor.over && (
          <Chip
            size="small"
            variant="outlined"
            label={`ruled out ${factor.over} here`}
            sx={{ mt: 1, borderStyle: 'dashed', color: 'text.secondary' }}
          />
        )}
      </Node>
    </Box>
  );
}

function TerminalNode({ number, method }: { number: number; method: string }) {
  return (
    <Box component="li" sx={{ display: 'flex', gap: 1.5 }}>
      <Rail last />
      {/* The terminal (method) node takes a 2px border rather than the 1px every other
          node uses — the one non-colour carrier DESIGN.md asks for beyond the connecting
          line, so the destination is identifiable even without colour. */}
      <Node number={number} terminal>
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
  number,
  terminal = false,
  children,
}: {
  number: number;
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
        position: 'relative',
      }}
    >
      <Typography
        variant="caption"
        sx={{
          position: 'absolute',
          top: -10,
          left: 8,
          bgcolor: 'background.paper',
          px: 0.5,
          color: 'text.secondary',
        }}
      >
        {number}
      </Typography>
      {children}
    </Box>
  );
}
