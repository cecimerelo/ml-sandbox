/**
 * The MUI theme — which is mostly MUI's theme.
 *
 * `DESIGN.md` is explicit that the default light theme *is* the design: `primary.main`,
 * the typography ramp, `shape.borderRadius` and `spacing()` are all left alone. The
 * product is a playground with a lab coat on, and the entire design budget is spent on the
 * charts. Overriding chrome here would be spending it twice.
 *
 * So this file sets only what the layout arithmetic needs.
 */

import { createTheme } from '@mui/material/styles';

import { spacing } from './tokens';

export const theme = createTheme({
  spacing: spacing.unit,
  components: {
    MuiButton: {
      // Shouting at the user in a product whose whole posture is restraint.
      styleOverrides: { root: { textTransform: 'none' } },
    },
  },
});
