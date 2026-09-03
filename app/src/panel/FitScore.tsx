import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';

import { chart, series } from '../theme/tokens';
import { fitScore } from './types';

/**
 * The engine's 0–1 score for one method: the numeral, then a bar.
 *
 * **One hue at one step.** The bar does not change colour by threshold. Threshold
 * colouring would spend the reserved status palette on a continuous quantity and assert a
 * quality judgement the engine does not make — the engine predicts a distance below the
 * best available method, not a verdict on whether that is good.
 *
 * **The number is never omitted.** The bar is the glance; the number is the value, and at
 * these magnitudes the bars are nearly identical because the methods nearly are.
 */
export function FitScore({ shortfall, compact = false }: { shortfall: number; compact?: boolean }) {
  const score = fitScore(shortfall);

  return (
    <Box>
      <Typography
        sx={{ fontSize: compact ? '1.5rem' : '2.5rem', lineHeight: 1.1, fontWeight: 400 }}
      >
        {score.toFixed(2)}
      </Typography>
      <Box
        role="meter"
        aria-valuenow={Number(score.toFixed(2))}
        aria-valuemin={0}
        aria-valuemax={1}
        aria-label="fit score"
        sx={{
          height: 8,
          borderRadius: 999,
          bgcolor: chart.gridline.hex,
          overflow: 'hidden',
          mt: 0.5,
        }}
      >
        <Box sx={{ width: `${score * 100}%`, height: '100%', bgcolor: series[1].hex }} />
      </Box>
      <Typography variant="body2" color="text.secondary" sx={{ mt: 0.5 }}>
        fit score · 0–1
      </Typography>
    </Box>
  );
}
