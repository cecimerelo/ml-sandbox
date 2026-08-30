import AppBar from '@mui/material/AppBar';
import Toolbar from '@mui/material/Toolbar';
import Typography from '@mui/material/Typography';
import { Link as RouterLink } from 'react-router-dom';

import { chrome, spacing } from '../theme/tokens';
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
  return (
    <AppBar
      position="static"
      elevation={0}
      // A coloured bar separates itself from the page; the divider hairline the white
      // version needed would be drawing a line that is already there.
      sx={{ bgcolor: chrome.topBar.hex }}
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
          sx={{ color: 'common.white', textDecoration: 'none', flexGrow: 1 }}
        >
          ML Sandbox
        </Typography>

        {/* The `Benchmark` link the spine specifies is not here yet: the surface it
            points at is empty until Epic 6. A link to a blank page spends the user's
            attention and returns nothing, which is worse than not offering it. It comes
            back with the evidence it is meant to show, together with the recommendation
            panel's `Where does this come from?` link to the same place. */}
      </Toolbar>
    </AppBar>
  );
}
