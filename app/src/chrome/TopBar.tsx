import AppBar from '@mui/material/AppBar';
import Toolbar from '@mui/material/Toolbar';
import Typography from '@mui/material/Typography';
import { Link as RouterLink } from 'react-router-dom';

import { chrome, spacing } from '../theme/tokens';
import { SkipLink } from './SkipLink';

/**
 * Block 0 — the product's only navigation furniture, on both surfaces.
 *
 * **Sticky**, by direct instruction (D-051) — it used to scroll away on the reasoning
 * that the collapsed form summary bar was the product's one sticky element and a second
 * one would compete with it for the same edge. In practice, losing the way back to the
 * product's name and home link on a long results page read as broken, not as restraint.
 * The product's only sticky element, now (D-052) — the summary bar itself is not.
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
      position="sticky"
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
