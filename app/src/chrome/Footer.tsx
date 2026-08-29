import Box from '@mui/material/Box';
import Link from '@mui/material/Link';
import Typography from '@mui/material/Typography';

import { spacing } from '../theme/tokens';

/**
 * Block 7 — present on both surfaces.
 *
 * The privacy link is a placeholder until 2.8 builds the notice. It is here now because
 * the spine makes it a persistent footer link on both surfaces, and a persistent element
 * added late tends to arrive on one surface and not the other.
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
          <Link href="#privacy">Privacy notice</Link>
        </Typography>
      </Box>
    </Box>
  );
}
