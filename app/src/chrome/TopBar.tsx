import AppBar from '@mui/material/AppBar';
import Button from '@mui/material/Button';
import Toolbar from '@mui/material/Toolbar';
import Typography from '@mui/material/Typography';
import { Link as RouterLink, useLocation } from 'react-router-dom';

import { spacing } from '../theme/tokens';
import { SkipLink } from './SkipLink';

/**
 * Block 0 — the product's only navigation furniture, on both surfaces.
 *
 * **Not sticky, and that is load-bearing.** The collapsed form summary bar is the single
 * sticky element in the product: it is the one-click route back to the inputs from the
 * bottom of a very long page. A second permanently-parked bar would compete with it for
 * the same edge on the same scroll, so this one scrolls away.
 *
 * It sits above the page plane by position and its divider, never by shadow — hence
 * `elevation={0}`.
 *
 * Nothing else belongs here. No logo, no menu, no avatar, no search, no breadcrumb, no
 * drawer: two surfaces do not need navigation, they need a way back.
 */
export function TopBar() {
  const onBenchmark = useLocation().pathname === '/benchmark';

  return (
    <AppBar
      position="static"
      elevation={0}
      sx={{
        bgcolor: 'background.paper',
        borderBottom: 1,
        borderColor: 'divider',
      }}
    >
      <SkipLink />
      <Toolbar
        sx={{
          minHeight: `${spacing.appBarHeight}px !important`,
          maxWidth: spacing.contentMax,
          width: '100%',
          mx: 'auto',
          px: { xs: `${spacing.pageMarginCompact}px`, md: `${spacing.pageMargin}px` },
        }}
      >
        <Typography
          variant="h6"
          component={RouterLink}
          to="/"
          sx={{ color: 'text.primary', textDecoration: 'none', flexGrow: 1 }}
        >
          Which method should I use?
        </Typography>

        <Button
          component={RouterLink}
          to="/benchmark"
          // On its own surface it is the current page, not somewhere to go. Announcing it
          // as a link would send a screen-reader user to where they already are.
          {...(onBenchmark ? { 'aria-current': 'page' as const } : {})}
        >
          Benchmark
        </Button>
      </Toolbar>
    </AppBar>
  );
}
