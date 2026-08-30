import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';

import { spacing } from '../theme/tokens';

/**
 * Block 7 — present on both surfaces.
 *
 * **The privacy link is not here yet.** The spine makes it a persistent footer link and
 * 2.8 builds the notice, but the notice has to be true of what the system does, and right
 * now the system does none of what it would describe: there is no upload to process in
 * memory and no session record to anonymise. Writing it now would mean promising things
 * about code that does not exist, which is the failure 2.8 exists to prevent — if the
 * implementation cannot honour a sentence, the sentence changes, not the other way round.
 *
 * The footer stays, so the link has somewhere to land once 3.1 and 2.7 give it something
 * to describe.
 */
export function Footer() {
  return (
    <Box
      component="footer"
      sx={{
        borderTop: 1,
        borderColor: 'divider',
        mt: `${spacing.sectionGap}px`,
        py: 3,
      }}
    >
      <Box
        sx={{
          maxWidth: spacing.contentMax,
          mx: 'auto',
          px: { xs: `${spacing.pageMarginCompact}px`, md: `${spacing.pageMargin}px` },
        }}
      >
        <Typography variant="body2" color="text.secondary">
          A study of how well textbook advice predicts which method actually wins.
        </Typography>
      </Box>
    </Box>
  );
}
