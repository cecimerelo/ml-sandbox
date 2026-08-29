/**
 * Design tokens — the values `DESIGN.md` specifies, in one place.
 *
 * The spine rules out a design-system epic: tokens are built by the first thing that needs
 * them, which is the top bar. So this file holds what that needs and grows as surfaces do,
 * rather than being a speculative system.
 *
 * MUI's default light theme *is* the design. This file carries only what MUI has no
 * opinion about — chiefly the chart palette, which is where the entire design budget went.
 *
 * Colours carry their measured accessibility properties, not just their hex. A palette
 * validated in a document nobody reopens is a palette that drifts; carried as data, the
 * constraint travels with the value and `tokens.test.ts` recomputes it in CI.
 */

/** A colour, with what was measured about it against the white chart surface. */
export interface Token {
  hex: string;
  /** WCAG contrast against `#ffffff`, as published in `DESIGN.md`. Recomputed in tests. */
  contrast: number;
  /**
   * Set when the value sits below the 3:1 floor for non-text marks. Not a dismissal — a
   * hard requirement that any chart using it ships a relief channel: direct labels on the
   * marks, or the table view. The rule is load-bearing, so it travels with the colour
   * rather than living in prose.
   */
  needsReliefChannel?: true;
}

const t = (hex: string, contrast: number, needsReliefChannel?: true): Token => ({
  hex,
  contrast,
  ...(needsReliefChannel ? { needsReliefChannel } : {}),
});

/**
 * UI chrome — MUI defaults, deliberately. There is no brand colour: the product has no
 * brand to express, and inventing one is the elaborate system that was ruled out.
 */
export const chrome = {
  primary: t('#1976d2', 4.6),
  textPrimary: t('#212121', 16.1),
  textSecondary: t('#666666', 5.74),
  textDisabled: t('#9e9e9e', 2.68),
  backgroundDefault: t('#fafafa', 1.03),
  backgroundPaper: t('#ffffff', 1.0),
  divider: t('#e0e0e0', 1.28),
} as const;

/**
 * Categorical chart slots — identity, assigned in order, never cycled and never reordered.
 * Colour follows the entity, not the rank: slot 1 is always the recommended method.
 */
export const series = {
  1: t('#2a78d6', 4.42),
  2: t('#eb6834', 3.2),
  3: t('#1baf7a', 2.82, true),
  4: t('#eda100', 2.17, true),
  /** The "Other" fold — always directly labelled, never a real series. */
  other: t('#757575', 4.61),
} as const;

/**
 * `series-3` and `series-4` fall below the 3:1 mark floor. Any chart reaching for them
 * must ship direct labels or the table view.
 */
export const SERIES_NEEDING_RELIEF = [3, 4] as const;

/**
 * The series cap differs by chart form, and it is a constraint rather than a style note.
 * Four slots all-pairs fails the normal-vision floor at yellow↔orange (ΔE 13.7, floor 15):
 * they are genuinely hard to separate when they touch, even with full colour vision.
 */
export const SERIES_CAP = {
  /** Overlaid lines, grouped and stacked bars — only neighbours touch. */
  adjacentOnly: 4,
  /** Scatter, decision boundaries, small multiples — any two marks can end up side by side. */
  anyPairMayTouch: 3,
} as const;

/** Chart furniture — the ink and rules a plot is drawn on. */
export const chart = {
  surface: t('#ffffff', 1.0),
  ink: t('#212121', 16.1),
  inkMuted: t('#666666', 5.74),
  axis: t('#bdbdbd', 1.9),
  gridline: t('#e0e0e0', 1.28),
} as const;

export const spacing = {
  /** MUI's `spacing()` unit. */
  unit: 8,
  appBarHeight: 64,
  /** The content column is centred and never exceeds this. */
  contentMax: 1440,
  pageMargin: 32,
  pageMarginCompact: 16,
  /** Between major blocks — the largest gap in the system. It says a new idea started. */
  sectionGap: 40,
  fieldGap: 16,
} as const;

/**
 * Dark mode is out of scope, and this palette cannot be flipped into it.
 *
 * Every value above is validated against the white chart surface and against nothing else.
 * A CSS filter, a `prefers-color-scheme` query or `palette.mode: 'dark'` will fail these
 * gates: inversion does not preserve the CVD separation ordering. Adding dark mode means
 * re-stepping the whole chart palette against a dark surface and re-running the validator.
 * It is a day of colour work, not a theme toggle.
 */
export const SUPPORTS_DARK_MODE = false;
