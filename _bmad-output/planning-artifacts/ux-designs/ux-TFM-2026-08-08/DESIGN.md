---
status: draft
updated: 2026-08-08
project: TFM
ui_system: MUI
name: TFM Recommender
description: Visual identity for an explainable supervised-learning method recommender. MUI (Material UI) light theme, near-default; the delta is a validated ~29-chart data-visualization system and the states that carry uncertainty (fit score, delta %, disabled-with-reason, stale).
sources:
  - ../../prds/prd-TFM-2026-07-26/prd.md
  - ../../prds/prd-TFM-2026-07-26/addendum.md
  - ./.memlog.md
colors:
  # --- UI chrome: MUI defaults, kept. Listed here only because charts must
  # --- coordinate with them. Anything not listed inherits MUI's default light palette.
  primary: '#1976d2'                # MUI palette.primary.main — DEFAULT, unchanged
  primary-contrast: '#ffffff'       # MUI palette.primary.contrastText — DEFAULT
  text-primary: '#212121'           # composite of MUI rgba(0,0,0,0.87) on white
  text-secondary: '#666666'         # composite of MUI rgba(0,0,0,0.60) on white
  text-disabled: '#9e9e9e'          # composite of MUI rgba(0,0,0,0.38) on white
  divider: '#e0e0e0'                # composite of MUI rgba(0,0,0,0.12) on white
  background-default: '#fafafa'     # MUI palette.background.default — DEFAULT
  background-paper: '#ffffff'       # MUI palette.background.paper — DEFAULT
  # --- Chart surface & ink (chart layer only; never used for UI chrome)
  chart-surface: '#ffffff'
  chart-ink: '#212121'
  chart-ink-muted: '#666666'
  chart-gridline: '#e0e0e0'
  chart-axis: '#bdbdbd'
  # --- Categorical series slots. Fixed order. Never cycled, never reordered.
  series-1: '#2a78d6'
  series-2: '#eb6834'
  series-3: '#1baf7a'
  series-4: '#eda100'
  series-other: '#757575'         # MUI grey[600]. Shifted from grey[500] #9e9e9e — see § Colors.
  # --- Sequential ramp (magnitude: benchmark heatmap, confusion matrix, |r|)
  seq-100: '#cde2fb'
  seq-200: '#9ec5f4'
  seq-250: '#86b6ef'
  seq-300: '#6da7ec'
  seq-400: '#3987e5'
  seq-500: '#256abf'
  seq-600: '#184f95'
  seq-700: '#0d366b'
  # --- Diverging ramp (polarity: correlation -1..+1, signed residuals, signed coefficients)
  div-neg-700: '#0d366b'
  div-neg-500: '#256abf'
  div-neg-300: '#6da7ec'
  div-neg-100: '#cde2fb'
  div-mid: '#f0efec'
  div-pos-100: '#fad6d2'
  div-pos-300: '#e4857e'
  div-pos-500: '#b13f3c'
  div-pos-700: '#621b1a'
  # --- Status. Reserved meaning. Never used as a series color, never used as an
  # --- ordinal quality scale (see components.method-characteristics-table).
  status-good: '#0ca30c'
  status-warning: '#fab219'
  status-serious: '#ec835a'
  status-critical: '#d03b3b'
  # --- Delta % is NEUTRAL INK by author decision — there are no delta-up / delta-down
  # --- colours. Direction is carried by the ▲ / ▼ glyphs and by `tied`. See § Colors.
  delta-tied: '#666666'
typography:
  # All UI roles inherit MUI's default Roboto ramp. Only chart-layer roles and two
  # numeric-display roles carry literal values.
  # Role names are semantic, not MUI's ramp names, because this file's role ladder is
  # two steps shorter than MUI's: the product has no h1/h2/h3/h5 role at all. Naming the
  # page title `h1` while it renders MUI `h4` would have been two names for one thing.
  page-title:
    note: 'MUI typography.h4 (34px/400) — page title, once per surface. DEFAULT, unchanged.'
  section-heading:
    note: 'MUI typography.h6 (20px/500) — section headings and the top-bar product title. DEFAULT, unchanged.'
  body:
    note: 'MUI typography.body1 (16px/400/1.5) — recommendation prose. DEFAULT, unchanged.'
  body-educational:
    note: 'MUI typography.body2 (14px/400/1.43) at {colors.text-secondary} — the inline explanation under every form question. DEFAULT size; color override only.'
  caption:
    note: 'MUI typography.caption (12px/400/1.66) — DEFAULT, unchanged.'
  fit-score-value:
    fontFamily: Roboto
    fontSize: 40px
    fontWeight: '400'
    lineHeight: '1.1'
    letterSpacing: -0.01em
  metric-value:
    fontFamily: Roboto
    fontSize: 20px
    fontWeight: '500'
    lineHeight: '1.2'
    fontVariantNumeric: tabular-nums
  chart-title:
    fontFamily: Roboto
    fontSize: 14px
    fontWeight: '500'
    lineHeight: '1.4'
  chart-subtitle:
    fontFamily: Roboto
    fontSize: 12px
    fontWeight: '400'
    lineHeight: '1.4'
  chart-axis-label:
    fontFamily: Roboto
    fontSize: 12px
    fontWeight: '400'
    lineHeight: '1.3'
  chart-tick:
    fontFamily: Roboto
    fontSize: 11px
    fontWeight: '400'
    lineHeight: '1.2'
    fontVariantNumeric: tabular-nums
  chart-legend:
    fontFamily: Roboto
    fontSize: 12px
    fontWeight: '400'
    lineHeight: '1.3'
  chart-annotation:
    fontFamily: Roboto
    fontSize: 11px
    fontWeight: '500'
    lineHeight: '1.2'
rounded:
  # MUI shape.borderRadius default is 4px. Kept. One larger step added for plot panels.
  DEFAULT: 4px
  sm: 4px
  md: 8px
  full: 9999px
spacing:
  # MUI spacing() base of 8px is DEFAULT and unchanged. Tokens below are spacing() multiples.
  unit: 8px
  field-gap: 16px
  plot-gap: 24px
  page-margin: 32px
  page-margin-compact: 16px
  section-gap: 40px
  content-max: 1440px
  plot-min-width: 320px              # PANEL border-box floor. See § Layout & Spacing.
  plot-area-min: 288px               # drawing area floor inside a panel at the floor width
  plot-panel-padding: 24px
  plot-panel-padding-compact: 16px   # panels narrower than 400px, incl. all comparison columns
  plot-aspect: '4 / 3'
  plot-aspect-square: '1 / 1'
  heatmap-cell-min: 24px
  heatmap-row-header: 200px
  heatmap-col-header: 120px
  panel-scroll-max-height: 70vh
  app-bar-height: 64px
breakpoints:
  # Derived, not chosen. The arithmetic is published in § Responsive.
  comparison-4col: 1416px
  comparison-3col: 1100px
  comparison-2col: 800px
  single-column: 800px
components:
  app-bar:
    component: 'MUI AppBar position="static"'
    elevation: '0'
    background: '{colors.background-paper}'
    border-bottom: '1px solid {colors.divider}'
    height: '{spacing.app-bar-height}'
    inner-max-width: '{spacing.content-max}'
    inner-gutter: '{spacing.page-margin}'
    title: '{typography.section-heading}'
    title-color: '{colors.text-primary}'
    link: 'MUI Button variant="text", textTransform none'
    link-color: '{colors.primary}'
    shadow: 'none — never, including on scroll'
    sticky: 'no — the bar scrolls away with the page. The form summary bar is the only sticky element in the product.'
  plot-panel:
    background: '{colors.chart-surface}'
    border: '1px solid {colors.divider}'
    elevation: '0'
    radius: '{rounded.md}'
    padding: '{spacing.plot-panel-padding}'
    padding-compact: '{spacing.plot-panel-padding-compact}'
    hover-border: '{colors.primary}'
    title: '{typography.chart-title}'
  shared-metrics-row:
    background: '{colors.background-paper}'
    border: '1px solid {colors.divider}'
    radius: '{rounded.md}'
    padding: '{spacing.plot-panel-padding-compact}'
    row-gap: '{spacing.field-gap}'
    label: '{typography.caption}'
    label-color: '{colors.text-secondary}'
    value: '{typography.metric-value}'
    value-color: '{colors.text-primary}'
    reference-top-rule: '2px solid {colors.primary}'
    column-divider: '1px solid {colors.divider}'
    method-dot-size: 8px
    wrapped-case: 'below {breakpoints.comparison-4col}, when the plot columns wrap, the row keeps one column per method in its own horizontally scrollable container and no longer tracks the plot columns'
  comparison-results:
    note: 'FR-5.3 empirical artifact. MUI Table, default density.'
    reference-top-rule: '2px solid {colors.primary}'
    reference-right-border: '1px solid {colors.divider}'
    numeric-cell: '{typography.metric-value}'
    method-dot-size: 8px
  method-characteristics-table:
    note: 'FR-2.2 qualitative artifact. Theory, no data. Present in every mode including advice-only.'
    component: 'MUI Table, default density'
    header: '{typography.chart-title}'
    cell-word: '{typography.caption}'
    cell-word-color: '{colors.text-primary}'
    rating-dot-size: 8px
    rating-dot-gap: 4px
    rating-dot-filled: '{colors.seq-600}'
    rating-dot-empty-ring: '1px solid {colors.text-secondary}'
    recommended-row-background: '{colors.seq-100}'
    recommended-row-left-rule: '2px solid {colors.primary}'
  decision-flowchart:
    note: 'FR-2.2 method-selection flowchart. Rendered graph, not an image.'
    node-background: '{colors.background-paper}'
    node-border: '1px solid {colors.divider}'
    node-radius: '{rounded.sm}'
    node-padding: '{spacing.unit}'
    node-min-width: 120px
    node-max-width: 200px
    node-label: '{typography.chart-annotation}'
    node-label-color: '{colors.chart-ink}'
    terminal-node-border: '2px solid {colors.divider}'
    path-node-border: '2px solid {colors.series-1}'
    path-node-background: '{colors.seq-100}'
    path-edge: '2px solid {colors.series-1}'
    path-step-badge: '{typography.chart-tick}'
    untaken-edge: '1px dashed {colors.chart-axis}'
    untaken-label-color: '{colors.text-secondary}'
    edge-label: '{typography.chart-tick}'
    edge-label-halo: '2px {colors.chart-surface}'
    collapse-below-panel-width: 640px
  benchmark-heatmap:
    cell-min: '{spacing.heatmap-cell-min}'
    cell-gap: '2px {colors.chart-surface}'
    ramp: '{colors.seq-100} → {colors.seq-700}'
    row-header-width: '{spacing.heatmap-row-header}'
    col-header-height: '{spacing.heatmap-col-header}'
    header-typography: '{typography.chart-tick}'
    sticky-headers: 'row header column and column header band both sticky'
    max-height: '{spacing.panel-scroll-max-height}'
    marker-glyph: '✓ / ✗ in {colors.chart-ink} or {colors.chart-surface} by cell darkness'
    legend: '{typography.chart-legend}'
  correlation-heatmap:
    aspect: '{spacing.plot-aspect-square}'
    max-features: 30
    annotate-max-features: 20
    cell-min: '{spacing.heatmap-cell-min}'
    cell-gap: '2px {colors.chart-surface}'
    ramp: '{colors.div-neg-700} → {colors.div-mid} → {colors.div-pos-700}'
    matrix-border: '1px solid {colors.chart-axis}'
    caption: '{typography.caption}'
  tree-diagram:
    node-background: '{colors.background-paper}'
    node-border: '1px solid {colors.divider}'
    node-radius: '{rounded.sm}'
    node-min-width: 88px
    node-label: '{typography.chart-annotation}'
    edge: '1px solid {colors.chart-axis}'
    max-depth: 4
    truncation-node-border: '1px dashed {colors.chart-axis}'
    truncation-node-color: '{colors.chart-ink-muted}'
    leaf-fill: '{colors.seq-100} → {colors.seq-700} on predicted value'
    caption: '{typography.caption}'
  fit-score-meter:
    track: '{colors.divider}'
    fill: '{colors.series-1}'
    value: '{typography.fit-score-value}'
    height: 8px
    radius: '{rounded.full}'
  delta-badge-up:
    foreground: '{colors.text-primary}'
    background: transparent
    glyph: '▲'
  delta-badge-down:
    foreground: '{colors.text-primary}'
    background: transparent
    glyph: '▼'
  delta-badge-tied:
    foreground: '{colors.delta-tied}'
    background: transparent
    glyph: '='
  method-chip:
    note: 'MUI Chip variant=outlined, DEFAULT sizing'
    selected-background: '{colors.primary}'
    selected-foreground: '{colors.primary-contrast}'
  method-chip-disabled:
    border: '{colors.divider}'
    foreground: '{colors.text-disabled}'
    icon: 'InfoOutlined 16px'
    icon-foreground: '{colors.text-secondary}'
    reason-foreground: '{colors.text-secondary}'
    reason-typography: '{typography.caption}'
  stale-results:
    opacity: '0.55'
    filter: 'saturate(0.5)'
    banner: 'MUI Alert severity=info variant=standard — DEFAULT'
  form-summary-bar:
    background: '{colors.background-paper}'
    elevation: '1'
    radius: '{rounded.sm}'
    position: sticky
---

## Brand & Style

TFM is a **playground with a lab coat on**. It is a thesis artifact, so it has to read as credible; it is also the first thing a person with zero ML background will meet, so it must not read as an instrument. The resolution is not decoration — it is *restraint plus evidence*. The page is quiet, near-stock Material, generously spaced, and then it gets loud in exactly one place: the plots. Charts are the product. Everything around them is scaffolding that gets out of the way.

The design discipline is therefore inverted from a normal app. Instead of "brand the chrome, keep the charts neutral," TFM **keeps the chrome stock and spends its entire design budget on the visualization system**. Roughly 20 method-specific plot types, 4 EDA plots, the 4-item FR-4.4 optional library, the method-selection flowchart, and the benchmark heatmap — **~29 distinct chart implementations** — have to read as one system, on one page, sometimes three or four abreast. If a reader can look at a residual plot, a ROC curve, and the benchmark heatmap and tell they came from the same tool without reading a label, this file did its job.

Concretely: **MUI's default light theme is the design.** `palette.primary.main`, the `typography` ramp, `shape.borderRadius`, and `spacing()` are all left at their defaults. This file specifies only what MUI has no opinion about — a validated chart palette, a chart-specific type scale, the layout arithmetic of the comparison grid, the visual treatment of uncertainty (fit score, delta %), and the two non-standard states this product needs (disabled-with-reason, stale).

### Dark mode is out of scope, and this palette cannot be flipped into it

Dark mode is **out of scope for v1.** `[ASSUMPTION — not stated in the PRD or decision log; inferred from "simple UI" + desktop-first + no auth / no saved preferences.]`

That assumption is about *scope*. The following is not an assumption, it is a measured fact about this file:

> **Every colour in this document is validated against the light chart surface `{colors.chart-surface}` `#ffffff` and against nothing else.** Contrast ratios, the CVD ΔE separations, the lightness band, the chroma floor, the "start no lighter than `seq-250`" rule for discrete chips, and the diverging ramp's lightness-matched arms are all computed against white. **A CSS `filter: invert()` / `hue-rotate()` flip, a `prefers-color-scheme` media query, or an MUI `palette.mode: 'dark'` switch will fail these gates.** Inversion does not preserve ΔE ordering, and it turns the diverging midpoint `{colors.div-mid}` `#f0efec` — already the weakest link at **1.11:1 on white** — into a near-black that reads as a *strong* value rather than as zero.
>
> Adding dark mode means re-stepping the whole chart palette against a dark surface and re-running the validator: 4 categorical slots re-picked, both ramps re-stepped, all 9 contrast ratios and both CVD pairlists recomputed. Budget it as a day of colour work, not a theme toggle. **Anyone who adds a dark theme without doing that has silently broken every accessibility claim in § Data Visualization → Accessibility.**

## Colors

### UI chrome — MUI defaults, deliberately

| Role | Value | Note |
|---|---|---|
| `palette.primary.main` | `#1976d2` | **MUI default. Not overridden.** 4.60:1 on `#ffffff`; white label on it is also 4.60:1, clearing 4.5:1 for button text. |
| `palette.secondary` / `error` / `warning` / `info` / `success` | MUI defaults | Not overridden. Used by MUI's own components (Alert, Snackbar, field validation) only — **never inside a chart.** |
| `palette.text.primary` / `.secondary` / `.disabled` | MUI defaults | 16.10:1 / 5.74:1 / 2.68:1 on `#ffffff`. |
| `palette.background.default` / `.paper` | `#fafafa` / `#ffffff` | MUI defaults. Page plane is `default`; the top bar, the form block, and every plot panel sit on `paper`. |
| `palette.divider` | `rgba(0,0,0,0.12)` → `#e0e0e0` | MUI default. Carries all separation in the layout — see Elevation. |

There is **no brand color**. The product has no brand to express, and adding one would be exactly the elaborate system the author ruled out. The blue you see is Material's blue.

**The one thing worth naming:** the app's chrome blue `{colors.primary}` `#1976d2` and the chart's `{colors.series-1}` `#2a78d6` are the same hue family at *different steps*, on purpose. Chrome blue is one step darker so white button text clears 4.5:1; series-1 is one step lighter so it reads as a mark rather than as a control. They never sit adjacent in a way that requires telling them apart — chrome is chrome, marks live inside plot panels. Do not "unify" them; you would break one contrast gate or the other.

### Chart color — four jobs, no free choices

Every chart color does exactly one of four jobs. There is no fifth job and no ad-hoc color.

**1. Categorical (identity — which method, which series, which class).** Four fixed slots, assigned in order, **never cycled and never reordered**:

| Slot | Hex | Contrast vs `#ffffff` | Meaning in this product |
|---|---|---|---|
| `{colors.series-1}` | `#2a78d6` blue | 4.42:1 | **Always the recommended method.** Also: train split, fitted/predicted values, class A. |
| `{colors.series-2}` | `#eb6834` orange | 3.20:1 | First user-selected alternative. Also: validation/test split, class B. |
| `{colors.series-3}` | `#1baf7a` aqua | 2.82:1 ⚠ | Second alternative. Class C. |
| `{colors.series-4}` | `#eda100` yellow | 2.17:1 ⚠ | Third alternative. |
| `{colors.series-other}` | `#757575` gray | 4.61:1 | The "Other" fold — never a real series. |

Validated against surface `#ffffff`, light mode, adjacent pairlist: lightness band **PASS**, chroma floor **PASS**, CVD separation worst adjacent pair `#eb6834`↔`#1baf7a` **ΔE 9.2** (deuteranopia, Machado 2009 severity 1.0, OKLab ×100, target ≥ 8) **PASS**, normal-vision floor worst adjacent `#1baf7a`↔`#eda100` **ΔE 22.9** (floor ≥ 15) **PASS**.

#### Why `series-other` is `#757575` and not `#9e9e9e`

It **was** `#9e9e9e`, and that was two defects wearing one hex. `#9e9e9e` is byte-identical to `{colors.text-disabled}`, and — the part that actually matters — it does not survive the palette's own CVD gate:

| `series-other` candidate | Contrast on `#ffffff` | Worst CVD ΔE vs slots 1–4 | Verdict |
|---|---|---|---|
| `#9e9e9e` (MUI grey 500, the old value) | 2.68:1 ✗ (< 3:1 mark floor) | **4.6** vs `series-3` `#1baf7a` (deuteranopia) ✗ | **FAIL** |
| `#8a8a8a` | 3.45:1 ✓ | **4.9** vs `series-3` (deuteranopia) ✗ | FAIL |
| `#616161` (MUI grey 700) | 6.19:1 ✓ | 14.0 ✓ | passes the slot gate, but **ΔE 1.8 from `{colors.chart-ink-muted}` `#666666`** — indistinguishable from chart text and from the neutral reference line. Rejected. |
| **`#757575`** (MUI grey 600) | **4.61:1 ✓** | **10.5** vs `series-2` `#eb6834` (protanopia) ✓ | **PASS — adopted** |

Full separations for the adopted value, OKLab ΔE ×100, normal vision / protanopia / deuteranopia:

| `#757575` vs | Normal | Protanopia | Deuteranopia |
|---|---|---|---|
| `series-1` `#2a78d6` | 16.3 | 15.5 | 17.0 |
| `series-2` `#eb6834` | 20.6 | **10.5** | 17.5 |
| `series-3` `#1baf7a` | 17.7 | 15.8 | 11.2 |
| `series-4` `#eda100` | 25.8 | 22.5 | 26.7 |

Every pair clears the ≥ 8 CVD target, and every pair also clears the ≥ 15 normal-vision floor (worst 16.3, vs `series-1`). That second result matters more than it looks: **`series-other` is permitted to share a frame with slots 1–3** — the multiclass tail fold in a decision-boundary or class-conditional plot does exactly that — and `3 slots + Other` therefore has to validate **all-pairs**, not adjacent-only. It does: worst all-pairs CVD **ΔE 9.2**, worst all-pairs normal-vision **ΔE 16.3**. Under the old `#9e9e9e` it did **not** — `#9e9e9e`↔`series-3` was ΔE 4.6 under deuteranopia, so a green class and the Other fold were the same mark. This is the defect the shift actually fixes; the `text-disabled` duplication was the symptom that made it visible.

`series-other` is still a **fold, not a fifth identity**, and the fold is always directly labelled (`Other (N categories)`), so it is never separated by colour alone regardless.

Two further gates the shift also clears, both of which `#9e9e9e` failed or scraped:

- **Mark contrast.** `#757575` is **4.61:1** on `#ffffff`, so the Other bar clears the 3:1 non-text floor on its own — it does **not** join `series-3` / `series-4` on the ⚠ list. `#9e9e9e` was 2.68:1 and had been sitting on that list silently.
- **Against chart furniture.** `#757575` vs `{colors.chart-axis}` `#bdbdbd` is **ΔE 23.6** (it was 9.9 — a fold bar was nearly the colour of the axis rule); vs `{colors.chart-gridline}` `#e0e0e0` **ΔE 34.4**.

The residual is `#757575` vs `{colors.chart-ink-muted}` `#666666` at **ΔE 5.2**. That is accepted and it is not a collision, because the two never share a frame: `chart-ink-muted` is a **text and reference-line** role, `series-other` is a **fill**, and `series-other`'s only two uses — the EDA categorical bar chart's `Other` bar and the multiclass tail fold — belong to families where no neutral reference line is drawn. A 12px gray tick label and a 40px-tall gray bar are not confusable at ΔE 5.2 by form alone.

`#757575` is **MUI `grey[600]`** — a stock Material value, so this shift adds no invented colour to a file whose whole posture is that it has none.

⚠ **`series-3` and `series-4` sit below the 3:1 mark-contrast floor.** This is a WARN, not a dismissal: any chart using slot 3 or 4 **must** ship a relief channel — visible direct labels on the marks, or the table view. Hard rule, and load-bearing (see § Data Visualization → *Load-bearing accessibility specifications*).

**The series cap differs by chart form, and this is a real constraint, not a style note:**

- **Overlaid lines, grouped/stacked bars** (4-method ROC overlay, CV-error curves, error-by-iteration): up to **4 slots**. Only neighbours touch, so the adjacent gate applies, and it passes.
- **Scatter, decision-boundary regions, pairwise-feature scatter, small multiples** — any form where any two marks can end up side by side: **cap at 3 slots.** The 4-slot all-pairs run **FAILs** the normal-vision floor at `#eda100`↔`#eb6834` **ΔE 13.7** (< 15): yellow and orange are genuinely hard to separate when they touch, even with full colour vision. The first three validate all-pairs clean (worst CVD ΔE 9.2, worst normal-vision ΔE 24.0).
- **Consequence for multiclass:** a decision boundary with **more than 3 classes** does not get a 4th hue. It becomes small multiples (one-vs-rest, one facet per class, each facet single-hue `series-1`), or the tail folds into `series-other`. `[ASSUMPTION — the PRD does not bound class count for multiclass problems. This is the palette's answer, not a product decision: if the author wants 5-class boundaries in one frame, the answer is faceting, not more colours.]`

### The slot register — total for every selection sequence

**Colour follows the entity, never the rank.** The four slots are a **register**, not a queue, and the rule below is defined for every possible selection/deselection sequence within FR-5.1's 4-method cap. This replaces the earlier "a freed slot is never backfilled" rule, which was self-defeating at the cap (deselect one of three alternatives, select a replacement, and there is no slot 5 to give it).

1. **Slot 1 is permanently held by the recommended method** for the whole session. It is never released, because the recommended method is never deselectable (FR-5.2).
2. Slots 2, 3, 4 are held by the user-selected alternatives, assigned **in selection order**, never in fit-score order.
3. **Deselecting a method releases its slot.** The other held slots do **not** move. Nothing already on screen repaints.
4. **A newly selected method takes the lowest-numbered free slot.** At the cap this is necessarily the slot just released, which is exactly what makes the rule total.
5. **Re-selecting a method that was previously deselected gives it the lowest free slot like any other new selection** — it is not entitled to its old slot. If its old slot happens to be the lowest free one, it gets it back; that is a coincidence, not a guarantee.
6. **Nothing repaints except the panels belonging to the entering method.** Rule 3 guarantees the other columns are visually stable across any deselect; rule 4 guarantees the entering method always has a colour.

The register is stable within a session and is not affected by FR-5.4's ranking coming back and reshuffling the ordering. *Behavioral consequences — when the repaint happens, what the user sees during it — live in `EXPERIENCE.md § Chart Behavior Contract`.*

**2. Sequential (magnitude).** One hue — blue — light→dark, `{colors.seq-100}` `#cde2fb` → `{colors.seq-700}` `#0d366b`. Used for: the benchmark **dataset × method heatmap**, the **confusion matrix**, **absolute** correlation where sign is not shown, **variable inclusion proportions** (BART), decision-tree **leaf fills**, and the **ordinal rating dots** in the Method characteristics table. Never a rainbow. If two sequential encodings ever share a frame, the second takes an orange one-hue ramp built the same way `[ASSUMPTION — no current screen needs two at once]`.

The full `100`→`700` range is legal for *continuous* magnitude (heatmap cells), where the lightest step legitimately means "near zero" and may recede toward the surface. If a ramp is ever used for **discrete ordered chips** (tiers, buckets, rating dots), start no lighter than `{colors.seq-250}` `#86b6ef` (2.06:1) so the light end still clears the surface. `{colors.seq-600}` `#184f95` measures **8.10:1** on `#ffffff` and is the step used wherever a ramp colour has to survive as a small solid mark.

**3. Diverging (polarity).** Blue ↔ red with a **neutral gray** midpoint `{colors.div-mid}` `#f0efec`. Equal steps per arm; the red arm is lightness-matched to the blue arm step for step, so neither side visually outweighs the other.

| r | −1.0 | −0.6 | −0.3 | 0 | +0.3 | +0.6 | +1.0 |
|---|---|---|---|---|---|---|---|
| hex | `#0d366b` | `#256abf` | `#6da7ec` | `#f0efec` | `#e4857e` | `#b13f3c` | `#621b1a` |

`[ASSUMPTION — the red arm hexes (#fad6d2 / #e4857e / #b13f3c / #621b1a) are not in the dataviz reference palette; I generated them in OKLCH at the categorical red's hue (24.9°), lightness-matched to the documented blue arm. Verified: monotone lightness PASS, adjacent ΔL ≥ 0.06 PASS, single hue (1° spread) PASS. Pole separation blue #256abf ↔ red #b13f3c: CVD ΔE 20.6, normal-vision ΔE 27.0 — both clear.]`

Used for: the **correlation heatmap** (the case that genuinely needs diverging — r runs −1..+1 and zero must read as "nothing"), **signed residual** shading, and **signed coefficient** plots. Zero is always the neutral gray. Never put a hue at the diverging midpoint.

**Delta % is not on this list.** It was, and it was wrong: a continuous diverging ramp and the three-state Delta badge are mutually exclusive encodings of the same quantity. The badge wins, because it carries a glyph and a word and the ramp cannot. `{colors.div-mid}` `#f0efec` is **1.11:1 on `#ffffff`** — legible as a heatmap cell inside a bordered matrix, never legible as a standalone text or badge colour.

**4. Status (state).** `{colors.status-good}` `#0ca30c` (3.35:1), `{colors.status-warning}` `#fab219` (1.79:1), `{colors.status-serious}` `#ec835a` (2.57:1), `{colors.status-critical}` `#d03b3b` (4.80:1). Reserved. A status colour is **never** "series 5," and **never** an ordinal quality scale — the Method characteristics table's five qualitative columns are ordinal, not status, and encoding them green/amber/red would spend the reserved palette and assert a judgment the theory layer does not make. Status always ships with an icon **and** a text label — warning and serious are deliberately sub-3:1 on white, and the icon+label pairing is the mitigation, not an oversight.

Status appears in: the per-method **timeout notice** (FR-8.4), **low-confidence auto-detection** flags (FR-8.2), **file rejection** (FR-8.1 / FR-8.5), and the benchmark page's **agree/disagree** marker. Note the collision rule: `status-critical` `#d03b3b` and the diverging ramp's red arm live in the same hue family — never let a status marker and a red-family mark share a frame relying on hue alone to separate them.

**Delta tokens — neutral ink, and the reason is methodological, not aesthetic.** Better and worse both render at `{colors.text-primary}` `#212121` (16.10:1) with a ▲ or ▼ glyph; tied renders at `{colors.delta-tied}` `#666666` (5.74:1) with `=` and the word `tied`. These are text colours, not fills, and **there is no green-up / red-down token** — the earlier `delta-up` `#006300` and `delta-down` `#d03b3b` are retired, and the `[ASSUMPTION]` that carried them is resolved rather than left open.

Green/red would say *beating the recommendation is a failure of the recommender*. This thesis is partly testing whether the recommender is correct, so an alternative outperforming it is a **finding**, not a failure — and colouring it as a failure would prime the user and bias the very behaviour § *Measurement Behavior* in `EXPERIENCE.md` is measuring. The direction is still fully carried, and by carriers that assert no valence: the **▲ / ▼ glyphs**, the literal word **`tied`**, and the sign of the number itself. Nothing is lost except an opinion the product is not entitled to have.

Reserving the delta from the status palette also keeps `{colors.status-good}` / `{colors.status-critical}` doing exactly one job, which is the same rule that keeps them out of the fit-score meter and out of the Method characteristics table.

## Typography

**MUI's default Roboto ramp is the spec for the entire UI.** No font is added; no size is overridden.

**Role names in this file are semantic; MUI's ramp names are the rendered values.** The product uses only two heading levels, so naming them `h1`/`h2` while they render MUI `h4`/`h6` would give one role two names and invite a developer to set the wrong one. The token names say what the text *is*; the note on each token says what MUI role to reach for. Roles map as:

- `{typography.page-title}` → MUI `h4` (34px/400) — page title, once per surface.
- `{typography.section-heading}` → MUI `h6` (20px/500) — section headings ("Recommendation", "Exploratory analysis", "Compare methods") and the top bar's product title.
- `{typography.body}` → MUI `body1` (16px/400) — the recommendation justification prose. This is the paragraph the whole product exists to deliver; it gets the largest readable body size, with the measure capped at **68ch** `[ASSUMPTION]`.
- `{typography.body-educational}` → MUI `body2` (14px/400) at `{colors.text-secondary}` `#666666` (5.74:1) — the **inline educational explanation under every form question** (FR-1.6). Size is MUI's default; only colour is overridden. This is the most-repeated text element in the product, so it must be visibly subordinate to its question label without ever dropping below 4.5:1.
- `{typography.caption}` → MUI `caption` (12px/400) — disabled-reason text, privacy notice, plot footnotes, truncation notices.
- `button` — MUI default, **except `textTransform: 'none'`**. `[ASSUMPTION — MUI's default uppercase button label reads institutional; sentence case supports "playground, not tutorial." This is the only typography override in the file and is a taste call the author should confirm or overrule.]`

**Numeric display roles** (not in MUI's ramp):

- `{typography.fit-score-value}` — 40px/400, proportional figures (it is a lone number). One per method card, for the 0–1 fit score.
- `{typography.metric-value}` — 20px/500, **`font-variant-numeric: tabular-nums`**. CV score (mean ± std), RMSE, accuracy, training time. Tabular is mandatory: these sit in the shared metrics row's aligned comparison columns and must not jitter between methods.

**Chart type scale.** Charts get their own smaller ramp so a plot panel never competes with the page heading. All Roboto — the chart layer must not introduce a second typeface.

| Role | Size / weight | Colour | Use |
|---|---|---|---|
| `{typography.chart-title}` | 14px / 500 | `chart-ink` `#212121` | One line above every plot. Names what the plot shows in plain language. |
| `{typography.chart-subtitle}` | 12px / 400 | `chart-ink-muted` `#666666` | The "what am I looking at" line. Optional in principle; the default for any plot a beginner won't recognise — which is most of them. Also carries every truncation disclosure (top-K, depth cap, facet cap). |
| `{typography.chart-axis-label}` | 12px / 400 | `chart-ink-muted` | Axis names. Always present, always units-bearing. |
| `{typography.chart-tick}` | 11px / 400, tabular | `chart-ink-muted` | Tick values, heatmap row/column headers, flowchart edge labels. Tabular figures mandatory. |
| `{typography.chart-legend}` | 12px / 400 | `chart-ink-muted` | Legend labels, including the benchmark heatmap's ramp and glyph legend. |
| `{typography.chart-annotation}` | 11px / 500 | `chart-ink` | Direct labels on marks, in-cell values, threshold callouts ("AUC = 0.87"), tree and flowchart node labels. |

**11px is the floor.** No chart text is ever rendered smaller, at any panel width, at any zoom. When labels will not fit at 11px, the chart truncates its content (top-K, depth cap) and says so in the subtitle — it does not shrink the type.

**Text never wears a series colour.** A legend label is `chart-ink-muted`; the colour swatch beside it carries identity. A direct label on an orange line is `chart-ink`, not orange. This is what keeps the sub-3:1 palette slots legible.

## Layout & Spacing

**MUI's 8px `spacing()` base is unchanged.** Every token below is a `spacing()` multiple.

The page is a single scrolling column of full-width blocks beneath a persistent top bar, following the locked decision that the form is a top block rather than a sidebar — the ~29 chart types need the page width more than the form needs persistence.

- `{spacing.page-margin}` **32px** = `spacing(4)` — left/right page gutter at ≥ `{breakpoints.single-column}`. Drops to `{spacing.page-margin-compact}` **16px** = `spacing(2)` below it.
- `{spacing.content-max}` **1440px** — the content column is centred and never exceeds it.
- `{spacing.section-gap}` **40px** = `spacing(5)` — between major blocks (form / recommendation / EDA / results / comparison). The largest gap in the system; it is what tells the reader a new idea started.
- `{spacing.plot-gap}` **24px** = `spacing(3)` — between plot panels in a grid, and the default internal padding of a plot panel.
- `{spacing.field-gap}` **16px** = `spacing(2)` — between form fields. The inline educational `body2` sits at `spacing(0.5)` (4px) below its field — tight, so it reads as attached to the question rather than floating between questions.

### The 320px floor, defined once

`{spacing.plot-min-width}` **320px** is the **panel border-box width**. Not the drawing area, not the SVG, not the content box. This is the number every breakpoint in § Responsive is derived from, and the ambiguity is resolved here so it is never re-litigated.

Panel padding is `{spacing.plot-panel-padding}` **24px** by default and `{spacing.plot-panel-padding-compact}` **16px** for any panel narrower than **400px** — which is every comparison column at every breakpoint. So at the floor:

```
320px panel − (2 × 16px compact padding) = 288px drawing area = {spacing.plot-area-min}
```

**288px is the drawing-area floor.** A chart that cannot render legibly at 288 × 216 (4:3) or 288 × 288 (1:1) is not a chart, it is a table — and it ships as one.

### Plot grid

MUI `Grid`, 12 columns. Method result plots render **2-up** (`xs={6}`) at ≥ `{breakpoints.comparison-3col}` **1100px**, 1-up below it. `{spacing.plot-aspect}` **4 / 3** is the default box; `{spacing.plot-aspect-square}` **1 / 1** is used by decision boundaries, correlation heatmaps, and confusion matrices, because both axes are the same kind of thing and squashing them lies about the geometry. Three chart forms carry **no fixed aspect at all** and set their own height: the benchmark heatmap, the decision-tree diagram, and the method-selection flowchart. See § Components.

Mixed aspects across a grid are now harmless, because **no cross-column row alignment is attempted anywhere in this product** — see below. The 1/1 override exists for geometric truth, and for no other reason.

### Comparison mode — shared metrics row, then free-flowing columns

Row alignment across method columns has been **removed as impossible**: FR-4.2 gives every method a *different* fixed plot set, so the intersection across four arbitrary methods is frequently empty and there is nothing to align. The structure is:

1. **A shared metrics row at the top**, genuinely aligned across all method columns, carrying only the quantities that are actually comparable: CV score (mean ± SD), accuracy or RMSE, training time, and delta % vs the reference column. This is the honest comparison object. Spec: `{components.shared-metrics-row}`.
2. **Below it, each method's own fixed plot set flows freely inside its own column**, at whatever height that method needs. **No cross-column row alignment is attempted or implied.** Column widths are equal; **column heights may differ, and that is correct** — it is what a method-specific plot set actually looks like.

Columns are separated by a `{colors.divider}` hairline running the full height of the block (the tallest column), never a background fill. Recommended method is leftmost as the reference column; column order is selection order.

**EDA** is a MUI `Accordion`, collapsed by default (locked upstream). Collapsed height is one `h6` row plus `spacing(2)` padding. The correlation heatmap inside it is **full-width**, spanning the whole EDA grid row — it is the one EDA chart that cannot live in a half-width panel (see § Components → *Correlation heatmap*).

## Responsive

Desktop-first, and **never "unsupported."** The page reflows; it does not have a cliff. `[ASSUMPTION removed — the earlier "below 900px the layout is unsupported" is retracted. It contradicted the 200%-zoom accessibility claim, since 200% zoom on a 1440px display yields a 720px CSS viewport.]`

### The breakpoint ladder

| Viewport | Comparison columns | Method-results plot grid | Page gutter | Everything else |
|---|---|---|---|---|
| ≥ `{breakpoints.comparison-4col}` **1416px** | **4** | 2-up | 32px | Content column capped at 1440px |
| **1100–1415px** | **3** | 2-up | 32px | 4th method's column wraps below the first three, keeping its slot colour |
| **800–1099px** | **2** | 1-up | 32px | Columns 3 and 4 wrap below |
| < `{breakpoints.single-column}` **800px** | **1** | 1-up | 16px | Whole page reflows to a single column; every block stacks |

### The arithmetic, published so it can be checked

Comparison column width at the bottom of each band, where `n` = column count:

```
column = (viewport − 2 × page-margin − (n − 1) × plot-gap) / n

4 cols @ 1416px : (1416 − 64 − 72) / 4 = 1280 / 4 = 320px  ✓ exactly the floor
4 cols @ 1440px : (1440 − 64 − 72) / 4 = 1304 / 4 = 326px  ✓
3 cols @ 1100px : (1100 − 64 − 48) / 3 =  988 / 3 = 329px  ✓
3 cols @ 1415px : (1415 − 64 − 48) / 3 = 1303 / 3 = 434px  ✓
2 cols @  800px : ( 800 − 64 − 24) / 2 =  712 / 2 = 356px  ✓
2 cols @ 1099px : (1099 − 64 − 24) / 2 = 1011 / 2 = 505px  ✓
```

`{breakpoints.comparison-4col}` is **derived, not chosen**: `4 × 320 + 3 × 24 + 2 × 32 = 1416`. The previous spec put the 4-column break at 1200px, which produced 278px panels — below the stated floor across the entire 1200–1416px range. That is fixed here and in every place the old math was implied.

**The 320px panel minimum is never violated at or above 800px.**

### Below 800px — the one place the panel floor yields

Below `{breakpoints.single-column}` the panel width becomes the content-box width, which can be less than 320px. The floor moves inward rather than breaking:

- The **panel** shrinks to the viewport. Nothing overflows the page.
- The **plot area inside the panel** keeps `{spacing.plot-area-min}` **288px** and **scrolls horizontally within its own panel** (`overflow-x: auto` on the plot area only).
- **There is never page-level horizontal scroll**, at any width, at any zoom. This is the claim `EXPERIENCE.md § Accessibility Floor` rests its 200%-zoom statement on, and it is the whole reason the cliff was removed.
- Charts whose intrinsic minimum exceeds 288px — the benchmark heatmap (770px), the correlation heatmap, wide tree diagrams — scroll inside their panels at *every* width, not only below 800px. Same mechanism, no special case.
- The method-selection flowchart does not scroll; it **collapses to a vertical step list** below 640px of panel width. See § Components.

### Zoom

200% browser zoom is handled by the same ladder: it is a viewport change, not a separate mode. 1440px @ 200% → 720px CSS → single column, no page-level horizontal scroll. WCAG 1.4.10 Reflow is measured at 320 CSS px; at 320px the page is single-column with in-panel chart scrolling, which is the criterion's own allowance for content requiring two-dimensional layout (data tables and charts). No claim is made that a 250,000-cell heatmap is comfortable at 320px — only that nothing is lost and nothing overflows the page.

## Elevation & Depth

**MUI's shadow scale is inherited; this file only restricts which levels are used.** The rule: *separation comes from hairlines and whitespace; elevation is reserved for things that genuinely float.*

- **Elevation 0** — every plot panel, every result card, the form block, **and the top bar**. `Paper elevation={0}` with a `1px solid {colors.divider}` border. This is the dominant treatment on the page. Twenty-nine shadowed cards would read as an instrument panel; flat bordered panels read as a worksheet.
- **Elevation 1** — the collapsed form-summary bar once it becomes sticky, and the stale-results banner.
- **Elevation 8 / 24** — MUI defaults for `Menu`, `Popover`, `Tooltip`, `Dialog`. Unchanged. Chart tooltips use MUI `Tooltip`'s default elevation so they match every other overlay in the app.

**Three elements sit above the page plane, and they do not all do it the same way:**

| Element | How it sits above | Why |
|---|---|---|
| **Top bar** (`{components.app-bar}`) | **Position only** — `position: static`, elevation **0**, a 1px `{colors.divider}` bottom hairline | It is above-plane because of **where it sits and what separates it**: it is the first thing on the page, on `background-paper` over a `background-default` plane, closed by a divider hairline. It is emphatically **not** above-plane by persistence — it is **not sticky** and scrolls away with the page (behavior: `EXPERIENCE.md § IA → Top bar`). A shadowed bar over 29 flat panels would be the loudest thing on a page whose loudest thing is supposed to be a chart. **No elevation-on-scroll**, ever — and with the bar non-sticky there is no scrolled state for it to have. |
| **Form summary bar** (`{components.form-summary-bar}`) | Elevation **1** | It leaves the flow and overlaps content that was above it. The shadow is what says "this is a copy of the block you scrolled past." |
| **Stale-results banner** (`{components.stale-results}`) | Elevation **1** | It sits over dimmed content at full opacity; the shadow separates the live thing from the past-tense thing. |

Nothing else gets a shadow. No hover-lift on plot panels; hover on an interactive panel is a border-colour change from `{colors.divider}` `#e0e0e0` to `{colors.primary}` `#1976d2` — a token pair, not a shadow. *When hover applies and what counts as an interactive panel: `EXPERIENCE.md § Component Patterns → Plot panel`.*

## Shapes

**MUI `shape.borderRadius` = 4px, unchanged.** Buttons, inputs, alerts, and small surfaces all inherit it.

- `{rounded.sm}` **4px** (= MUI default) — inputs, buttons, alerts, small surfaces, **chart tooltips**, flowchart nodes, and tree nodes.
- `{rounded.md}` **8px** — plot panels, result cards, and the shared metrics row only. These are the largest objects on the page; 4px on a 600px-wide panel reads as an accident. One step up is the entire customisation.
- `{rounded.full}` **9999px** — MUI `Chip` (already pill by default), the fit-score meter track, and the rating dots in the Method characteristics table. Nothing else — a "terminal" flowchart node is distinguished by a **2px border**, not by becoming a pill.

**Inside charts:** bar ends get a **4px radius on the value end only**, square at the baseline. Never round both ends — a floating capsule detaches the bar from its axis and misreads zero.

## Components

**Used as-is from MUI, unchanged:** `Button`, `TextField`, `Select`, `Autocomplete`, `Switch`, `RadioGroup`, `Slider`, `Accordion`, `Alert`, `Snackbar`, `Dialog`, `Tooltip`, `LinearProgress`, `CircularProgress`, `Table`, `Skeleton`. The contract is **do not restyle these.** Every hour spent theming a MUI Select is an hour not spent on the charts.

The components below are either brand-layer overrides or genuinely new to this product. **Behavior for all of them lives in `EXPERIENCE.md`;** this section specifies appearance only.

### Top bar

`{components.app-bar}`. The product's only navigation furniture, present on both surfaces.

- MUI `AppBar position="static"`, **`elevation={0}`**, background `{colors.background-paper}` `#ffffff`, with a **`1px solid {colors.divider}` bottom border**. It is above the page plane by position and its divider, not by shadow and not by persistence (see § Elevation & Depth). **It is not sticky** — it scrolls away with the page, leaving `{components.form-summary-bar}` as the product's single sticky element.
- Height `{spacing.app-bar-height}` **64px** — MUI's default desktop `Toolbar`. Inner content is capped at `{spacing.content-max}`, centred, with `{spacing.page-margin}` gutters, so the title aligns with the page's left edge and the link with its right edge.
- **Left:** the product title in `{typography.section-heading}` (MUI `h6`, 20px/500) at `{colors.text-primary}` `#212121` (16.10:1). It is a link to `/`.
- **Right:** exactly one MUI `Button variant="text"` reading `Benchmark`, at `{colors.primary}` `#1976d2` (4.60:1), `textTransform: none`.
- **Nothing else.** No logo mark, no menu, no avatar, no search, no breadcrumb, no tab bar, no drawer. Two surfaces do not need navigation; they need a way back.

### Plot panel

The atomic unit of the product. `Paper elevation={0}`, `1px solid #e0e0e0`, `{rounded.md}` 8px, `{colors.chart-surface}` `#ffffff`, padding `{spacing.plot-panel-padding}` 24px — or `{spacing.plot-panel-padding-compact}` 16px below 400px panel width.

Anatomy, top to bottom: `chart-title` (plain language, always) → optional `chart-subtitle` (the beginner-facing "what this shows", and the home of every truncation disclosure) → the plot at its aspect box → legend below the plot, left-aligned, horizontal → optional `caption` footnote. A **"View as table"** text button sits top-right.

**Structural rule:** the chart's graphic element (SVG / canvas) is the *only* part of the panel that is a graphic. Title, subtitle, legend, footnote, and the `View as table` button are ordinary DOM siblings **outside** it — never inside the element that carries the chart's `role="img"`, or the fallback becomes unreachable by the users it exists for.

**Table view geometry.** When toggled, the table renders **inside the same aspect box the chart occupied**, with internal vertical scroll and a sticky header row. The panel's outer height does not change, so the grid above it never reflows. Long value columns truncate with the full value on the cell; they never widen the panel.

### Shared metrics row (comparison mode)

`{components.shared-metrics-row}`. The **only** aligned object in comparison mode, and the reason comparison mode is honest.

- One block spanning the full comparison grid, `{rounded.md}` 8px, `1px solid {colors.divider}`, padding `{spacing.plot-panel-padding-compact}` 16px. It sits directly under the comparison section heading and above the columns, separated from them by `{spacing.plot-gap}` 24px.
- **Columns are the methods**, at the same widths and the same `{spacing.plot-gap}` gutters as the plot columns below, so the grid reads as one grid even though nothing below it aligns. **This holds only while the column counts match** — i.e. at ≥ `{breakpoints.comparison-4col}` **1416px** for a 4-method comparison.
- **When the plot columns wrap, the metrics row does not.** Below `{breakpoints.comparison-4col}` the plot grid drops to 3 (or 2) columns and the remaining method columns wrap to a second row, while **the metrics row keeps one column per method — all four — in its own container, scrolling horizontally inside that container** when they do not fit. It therefore stops tracking the plot columns' widths and gutters, and that is deliberate: the row's entire job is digit-for-digit comparability across *every* method at once, which a wrapped row cannot deliver. It is the one object in the block that never wraps. Below `{breakpoints.single-column}` **800px** it stops being a row at all and becomes a stacked metrics table — one row per method, the same four quantities. *Behavior and the per-breakpoint statement: `EXPERIENCE.md § Responsive & Platform`.*
- **Rows are the four comparable quantities**, in fixed order: **CV score (mean ± SD)** · **accuracy or RMSE** · **training time** · **delta % vs reference**. Row labels sit in a leftmost label column at `{typography.caption}` / `{colors.text-secondary}`. Row gap `{spacing.field-gap}` 16px.
- **Values** in `{typography.metric-value}` 20px/500 **tabular** at `{colors.text-primary}`. Tabular is not optional here — this is the one place in the product where four numbers must line up digit for digit.
- **Column headers** carry an 8px `series-N` dot before the method name. The dot is the **only** place a series colour appears in this block; every value stays in ink.
- **The reference column** (recommended method, leftmost) carries a **2px `{colors.primary}` top rule** and a `1px {colors.divider}` right border. Its delta cell reads `—` (em dash) at `{colors.text-secondary}`, never `0.0%`.
- **Delta cells** use `{components.delta-badge-up}` / `-down` / `-tied`. Text only.
- A method that timed out shows `—` at `{colors.text-secondary}` in every row plus a `{typography.caption}` note in its column header. It is not blank, and it is not zero.

### Comparison results (FR-5.3)

`{components.comparison-results}`. The **empirical** artifact, dataset-only. *(Renamed from "Comparison table" — the qualitative FR-2.2 artifact is the Method characteristics table, below. The two names never overlap again.)*

MUI `Table`, default density, with three deltas: (1) the recommended method's column carries a `{colors.divider}` right border and a 2px `{colors.primary}` top rule marking it as the reference; (2) all numeric cells use `{typography.metric-value}` with tabular figures; (3) an 8px `series-N` dot precedes each method name in the header, tying the row to its plots. The dot is the **only** place a series colour appears in the table — cell text stays in ink.

### Method characteristics table (FR-2.2)

`{components.method-characteristics-table}`. The **qualitative** artifact: theory, no data, **always present — including advice-only mode, where it is the only evidence artifact the product delivers.** It renders from the rule layer and never touches a dataset.

- MUI `Table`, default density. **Rows are methods** (recommended first, then the ranked alternatives). **Columns are the PRD's five qualitative axes:** accuracy potential · interpretability · training speed · handles non-linearity · handles missing values. Header in `{typography.chart-title}` 14px/500 at `{colors.chart-ink}`.
- **The recommended method's row** carries a `{colors.seq-100}` `#cde2fb` background tint and a **2px `{colors.primary}` left rule**. `{colors.text-primary}` `#212121` on `#cde2fb` measures **13.4:1**. No other row is tinted.

**Qualitative cell encoding — ordinal, three steps, never the status palette.**

Each cell carries **two carriers, both always present**: a word and a three-dot rating.

| Axis | Step 3 | Step 2 | Step 1 |
|---|---|---|---|
| Accuracy potential | `high` | `moderate` | `lower` |
| Interpretability | `high` | `moderate` | `low` |
| Training speed | `fast` | `moderate` | `slow` |
| Handles non-linearity | `yes` | `partly` | `no` |
| Handles missing values | `yes` | `partly` | `no` |

- **The word** is primary: `{typography.caption}` 12px at `{colors.text-primary}` `#212121` (16.10:1). It is what a screen reader gets and what survives print, forced-colors, and any CVD.
- **The dots** are the glance: three 8px circles, 4px apart, `{rounded.full}`. Filled dots are `{colors.seq-600}` `#184f95` (**8.10:1** on `#ffffff` — clears 3:1 for non-text content by a wide margin). Empty dots are unfilled with a `1px {colors.text-secondary}` `#666666` ring (5.74:1). Filled count = the step number.
- **All five axes read in the same direction: three dots is more of the named quality.** Three dots on *training speed* means fast. Three dots on *handles missing values* means yes. There is no axis where more dots is worse, so the reader never has to remember a polarity.
- **Never green/amber/red.** These are ordinal positions on a theory axis, not health states. Using `{colors.status-good}` / `{colors.status-warning}` / `{colors.status-critical}` here would spend the reserved status palette and assert a verdict the rule layer does not make — the same error the fit-score meter refuses.
- **Never a single hue varying by lightness alone across the row.** The dot *count* is the encoding; the fill colour is constant.
- Below `{breakpoints.single-column}` the table scrolls horizontally **inside its panel**, with the method-name column sticky. It does not reflow into cards.

### Method-selection flowchart (FR-2.2)

`{components.decision-flowchart}`. A **rendered graph, not a static image** — the user's own traversed path has to be distinguishable, which a PNG cannot do. It is not one of the plot families; it has no series, no axes, and no aspect ratio. It sits in the recommendation panel at full block width and takes whatever height it needs.

**Nodes.** `{colors.background-paper}` `#ffffff`, `1px solid {colors.divider}`, `{rounded.sm}` 4px, `{spacing.unit}` 8px padding, min width 120px, max width 200px. Label in `{typography.chart-annotation}` 11px/500 at `{colors.chart-ink}` `#212121`, max 2 lines, ellipsis beyond — the full text lives in the table view. **Terminal (method) nodes** are distinguished by a **2px** border instead of 1px; they do not become pills.

**Edges.** `1px solid {colors.chart-axis}` `#bdbdbd` with an arrowhead. Edge labels (the branch answers — `yes` / `no` / `> 10k rows`) in `{typography.chart-tick}` 11px at `{colors.chart-ink-muted}` `#666666`, each with a **2px `{colors.chart-surface}` halo** so it stays readable where it crosses a line.

**The traversed path vs. the untaken branches** — three carriers, because one of them is colour:

| | Traversed | Untaken |
|---|---|---|
| Node border | **2px `{colors.series-1}`** `#2a78d6` | 1px `{colors.divider}` `#e0e0e0` |
| Node fill | `{colors.seq-100}` `#cde2fb` | `{colors.background-paper}` `#ffffff` |
| Node label | `{colors.chart-ink}` `#212121` (13.4:1 on the tint) | `{colors.text-secondary}` `#666666` (5.74:1) — **subordinate, never disabled**; an untaken branch is information, not a dead control |
| Edge | **2px solid `{colors.series-1}`** | **1px dashed `{colors.chart-axis}`** |
| Marker | a numbered step badge `1`, `2`, `3`… in `{typography.chart-tick}` at the node's top-left corner | none |

Border weight, fill, dash pattern, and the step badges are all non-colour carriers. Remove colour entirely and the path is still the only sequence of 2px-bordered, badged nodes joined by solid lines.

**Degradation.** Below **640px of panel width** the flowchart **collapses to a vertical step list**: one row per traversed decision in order, each reading `question → answer`, with the untaken branch named in `{typography.caption}` beneath it. This is a layout swap, not a scaled-down diagram. There is **no pan, no zoom, and no scaling of text below 11px** — the diagram either fits at full size or becomes the list.

### Fit score meter

The engine's 0–1 score, one per method card.

- Numeral in `{typography.fit-score-value}` 40px at `{colors.text-primary}`, rendered to **two decimals** (`0.87`) `[ASSUMPTION — the PRD specifies the 0–1 range but not the precision]`.
- Below it, an 8px-tall track at `{rounded.full}`, `{colors.divider}` background, filled left-to-right in `{colors.series-1}` to the score's proportion, full card width.
- The bar is **one hue at one step** — it does **not** change colour by threshold. Threshold-colouring would spend the reserved status palette on a continuous quantity and assert a quality judgment the engine does not make. The number is the value; the bar is the glance.
- A `caption` under the track names the scale: `fit score · 0–1`. Never ship the bar without the numeral.

### Delta badge

The % change vs the recommended method, in the shared metrics row and in the FR-5.4 ranking.

- Better: `{colors.text-primary}` `#212121` (16.10:1), glyph `▲` — e.g. `▲ 4.2%`.
- Worse: `{colors.text-primary}` `#212121`, glyph `▼` — **the same ink**. Direction is the glyph and the sign, never the colour.
- Tied (within 1 std dev, per FR-5.4): `{colors.delta-tied}` `#666666` (5.74:1), glyph `=`, and the literal word **`tied`** rather than a number. This is the one delta state that is set apart, and it is set apart by being *recessive*, not by being a third opinion — a difference the data cannot support should read as quieter than one it can.
- The reference column shows `—` (em dash) at `text-secondary`, not `0.0%`.
- **Colour carries no valence here, in either direction.** Better and worse are the same ink; there is no green-up, no red-down, no status colour, and **no diverging ramp** — see § Colors for why. The glyph and the sign are the whole encoding, so the badge already satisfies "colour is never the sole carrier" by having no colour signal to be sole.
- Text only. No pill, no fill, no background.

### Method chip — and the disabled-with-reason state

MUI `Chip variant="outlined"`, default sizing. Selected: `{colors.primary}` fill, white label.

**Disabled with reason** (FR-8.3 — incompatible methods stay visible, never hidden):

- Outline stays at `{colors.divider}`; **no fill**; label drops to `{colors.text-disabled}` `#9e9e9e`.
- An `InfoOutlined` icon at **16px**, explicitly coloured `{colors.text-secondary}` `#666666` (**5.74:1**), is appended inside the chip. This is the non-colour carrier: a chip is disabled because it has the icon, not because it looks pale — and a carrier that inherits the 2.68:1 label colour at 12px is not a carrier, it fails WCAG 1.4.11 at the exact point it is load-bearing. **Do not let this icon inherit.**
- The reason renders as `caption` at **`{colors.text-secondary}` `#666666` (5.74:1)** — deliberately *not* `text.disabled` (2.68:1). The chip is disabled; **the explanation is not.** A reason a user cannot read is not a reason. This is the one place the product refuses MUI's disabled convention.

*Where the reason appears (tooltip vs. inline), focus behavior, and the `aria-disabled` contract: `EXPERIENCE.md § Component Patterns` and `§ Accessibility Floor`. This file previously prescribed a `<span>` wrapper, which is the MUI workaround for the real `disabled` attribute and contradicts EXPERIENCE.md's focusable `aria-disabled` chip. That prescription is withdrawn.*

### Stale results

When any form answer changes after a run (locked decision: dim + banner, non-destructive):

- The whole results region takes `opacity: 0.55` **and** `filter: saturate(0.5)`. Both together — opacity alone leaves saturated chart colours looking active; desaturation alone doesn't read as past tense. Text inside stays above 4.5:1 at 0.55 because it starts at 16.10:1.
- A MUI `Alert severity="info"` at elevation 1, sticky at the top of the results region. Full opacity, never dimmed.
- **Never animate the dim.** It should already be dim by the time the user's eye returns from the form.

*Which controls disable, what stays interactive, and the exit: `EXPERIENCE.md § State Patterns → Stale`.*

### Benchmark heatmap (FR-6.2)

`{components.benchmark-heatmap}`. The one chart that is also a data table, at a scale nothing else in the product reaches: **~72 OpenML-CC18 + UCI datasets × ~22 methods ≈ 1,600 cells.** It has **no `plot-aspect`** and does not live in the 4:3 grid — it sets its own geometry.

**Layout rule.**

- **Cells** are `{spacing.heatmap-cell-min}` **24 × 24px** minimum — the WCAG 2.5.8 target-size floor, and these cells are interactive. Cells grow to fill available width; they never shrink below 24px.
- **Row header column** `{spacing.heatmap-row-header}` **200px**, sticky left, holding the dataset name in `{typography.chart-tick}` truncated at 200px.
- **Column header band** `{spacing.heatmap-col-header}` **120px**, sticky top, holding method names in `{typography.chart-tick}` rotated 90° (reading bottom-to-top).
- **Intrinsic minimum width:** `200 + 22 × 24 + 21 × 2 = 770px`. Below that the grid **scrolls horizontally inside its own panel**, at every viewport, never at page level.
- **Height:** `120 + 72 × 24 + 71 × 2 = 1,990px`. The panel caps at `{spacing.panel-scroll-max-height}` **70vh** with internal vertical scroll and both header bands pinned. **Virtualize rows above 100** — the panel's scroll height must reflect the full row count so the scrollbar does not lie.
- **Row groups.** Two sticky sub-headers inside the scroll, in `{typography.chart-title}`: `Classification · OpenML-CC18` and `Regression · UCI`. This is also where dataset provenance (FR-6.3) becomes visible without a hover.
- **The panel is full-bleed** to `{spacing.content-max}` — it is never in a 2-up grid.

**Cell rendering.** Cells on the `seq-100`→`seq-700` blue ramp with a **2px `{colors.chart-surface}` gap** between cells so adjacent values never bleed together. Agree/disagree markers overlay as a glyph (`✓` / `✗`) in `chart-ink` or `chart-surface` depending on cell darkness — **the marker is a glyph, not a colour change**, so agreement survives both CVD and the ramp. No in-cell numbers: at 24px there is no room, and the number lives in the tooltip and the table view.

**Legend** (mandatory, sits above the grid, `{typography.chart-legend}`): a continuous ramp strip from `seq-100` to `seq-700` with its min and max values labelled, plus the two glyph keys — `✓ heuristic agrees with the benchmark` / `✗ disagrees`. A sequential ramp carrying two overlaid glyph states without a legend is unreadable.

**`View as table` is mandatory here, not optional**, and it is the primary reading mode for anyone using a screen reader.

**`Report an error` is a persistent per-row button** in a column at the right edge of the row-header block — **not** inside a hover tooltip. Tooltip content is not pointer-reachable and is not in the tab order, so an action placed there cannot be operated. *Tooltip contents and the roving-grid keyboard model: `EXPERIENCE.md`.*

### Correlation heatmap (FR-3.3)

`{components.correlation-heatmap}`. NFR-2 permits **500 features**, which is 250,000 cells; at 288px of drawing area that is 0.58px per cell. The chart does not attempt it.

- **Hard cap: the 30 highest-variance features.** Above 30 features the matrix truncates and the `{typography.chart-subtitle}` says so, verbatim in shape: `Showing the 30 features with the most variation, of 500.` The truncation is stated, never silent.
- **In-cell `r` values only at ≤ 20 features.** Between 21 and 30 the numbers are dropped and the value lives in the hover and the table view — `{typography.chart-annotation}` 11px does not fit in a sub-24px cell, and 11px is the floor.
- **Cells** `{spacing.heatmap-cell-min}` **24px** minimum, 2px `{colors.chart-surface}` gaps, `{spacing.plot-aspect-square}` **1 / 1**. Intrinsic minimum at 30 features: `30 × 24 + 29 × 2 = 778px` plus labels — so **the correlation heatmap is a full-width panel spanning the whole EDA grid row**, never a half-width one, and scrolls inside its panel below that width.
- **The matrix gets a `1px {colors.chart-axis}` `#bdbdbd` border around the whole cell block.** This is not decoration: `{colors.div-mid}` `#f0efec` is **1.11:1 on `#ffffff`**, so the near-zero region — which is most of a wide correlation matrix — is otherwise invisible against the surface and the matrix appears to have holes in it. The border, plus the 2px white cell gaps reading as a lattice, is what gives the near-zero field an edge.
- **Fewer than 2 numeric features** → the panel renders a `{typography.body}` line saying there is nothing to correlate, at the panel's normal height. It is not omitted, and it is not an error.

### Decision-tree diagram (FR-4.2)

`{components.tree-diagram}`. An unpruned tree on 14,000 rows has thousands of nodes and exceeds any panel by orders of magnitude. The visual rule is a **depth cap with an explicit truncation indicator** — not pan, not zoom, not scaling.

- **Nodes** on `{colors.background-paper}` with `1px {colors.divider}` borders, `{rounded.sm}` 4px, min width **88px**, label in `{typography.chart-annotation}` 11px at `{colors.chart-ink}`. Split conditions in the same role. Leaf nodes may take a `seq` fill on predicted value. **Never rainbow the branches.** Edges `1px solid {colors.chart-axis}`.
- **Depth cap: `4` levels, and lower if the level does not fit.** The rendered depth is the deepest level whose nodes fit at 88px minimum width inside the panel (allowing in-panel horizontal scroll up to 2× panel width), capped at 4 regardless. A depth-4 tree is 16 leaves ≈ 1,500px wide; a 320px panel will usually resolve to depth 2 or 3.
- **Truncated subtrees collapse to a single truncation node** — `1px dashed {colors.chart-axis}` border, label `⋯ N more splits` in `{typography.chart-annotation}` at `{colors.chart-ink-muted}` `#666666`. Every truncated branch gets one; a branch never just stops.
- **The subtitle states the truncation:** `Showing the first 3 of 11 levels.` Not the caption, not a tooltip — the subtitle, where every other truncation disclosure lives.
- **No pan/zoom control.** A drag-to-pan canvas is a bespoke interaction in a product whose interaction budget is spent; horizontal scroll inside the panel is the whole affordance.
- The full tree is not recoverable from the visual. That is a stated limitation, not a defect to design around.

## Data Visualization

This section is the reason this file exists. It governs ~20 method-specific plots, 4 EDA plots, the 4-item FR-4.4 optional library, and the benchmark heatmap — **~29 distinct chart implementations**. The goal is **one system**, recognisable across every method.

### Slot assignment by plot family

| Family | Plots | Colour job | Assignment |
|---|---|---|---|
| **Fit / residual** | residual plot, predicted-vs-actual scatter, fitted curve | categorical (1 series) + neutral reference | Marks in `series-1` at 60% opacity. The reference line (y = x, or y = 0) is **2px dashed `{colors.chart-axis}` `#bdbdbd`** — neutral, never coloured, because it isn't a series. Optional residual shading uses the diverging ramp on sign. |
| **Coefficients / importance** | coefficient plot, feature importance bar, variable inclusion proportions | nominal categorical → **one hue** | All bars `series-1`, sorted by magnitude, **top 20 shown** with a `{typography.caption}` fold line naming the remainder (`and 480 more`). Do **not** colour bars by their own value — length already encodes it, and spending the identity channel there is the classic error. Where sign matters (coefficients go negative), use the **diverging ramp**, not two categorical slots. |
| **Classification quality** | ROC curve, confusion matrix, calibration curve | ROC = categorical; matrix = sequential | ROC: one line per method, slots 1..4, plus a dashed `chart-axis` chance diagonal. Confusion matrix: `seq` ramp on cell value, `{spacing.plot-aspect-square}` 1/1, cells ≥ `{spacing.heatmap-cell-min}` 24px, and **every cell carries its number** in `chart-annotation` (white on `seq-500`+, `chart-ink` below) **up to 10 classes**; above 10 the numbers drop and the subtitle says so. The ramp is the glance; the number is the truth. |
| **Boundaries** | decision boundary (LDA / QDA / KNN / SVM), support-vector overlay | categorical, **≤ 3 classes** | `{spacing.plot-aspect-square}` 1/1. Filled regions at **18% opacity**; points at full opacity with a **2px `#ffffff` ring** so overlapping points stay countable. **Marker shape varies with class** (circle / triangle / square) — the mandated non-colour channel. Support vectors: same fill, `chart-ink` 1.5px stroke, ~1.4× radius. **Facet cap: 6.** Above 6 classes the boundary plot is not rendered at all and the panel carries a `{typography.body}` line saying so — 100 facets is not a visualization. |
| **Tuning curves** | accuracy-vs-K, CV-error-vs-lambda, variance-explained-vs-components, OOB error curve, **learning curve (FR-4.4)** | categorical (1–2 series) | 2px line in `series-1`. The chosen optimum gets a filled dot ≥ 8px plus a `chart-annotation` direct label (`K = 7`). CV error bands render as `series-1` at 15% fill, no stroke. |
| **Train-vs-validation pairs** | train-vs-test error by iteration, train-vs-validation loss, **learning curve's two curves** | **semantic pair** | Train = `series-1` `#2a78d6` **solid**; validation/test = `series-2` `#eb6834` **dashed (6 2)**. Fixed across the entire product. The dash pattern is the non-colour channel. Validated all-pairs: CVD ΔE 24.7, normal-vision ΔE 33.6. |
| **Actual-vs-predicted pairs** | predicted-vs-actual, posterior credible intervals, fitted curve, **calibration curve (FR-4.4)** | **semantic pair** | Actual / observed / the perfect-calibration diagonal = `{colors.chart-ink-muted}` `#666666`, dashed for the reference line — it is ground truth, not a competing series. Predicted / fitted = `series-1` `#2a78d6`. Credible and confidence intervals = `series-1` at 15% fill, no stroke. |
| **Shrinkage paths** | coefficient shrinkage path (Ridge / Lasso), partial dependence per feature | many thin lines | The one family that exceeds 4 series. **Do not generate hues.** All paths in `chart-ink-muted` at 40% opacity; the 3 largest-magnitude coefficients promote to slots 1–3 at full opacity with direct labels. Everything else is context. |
| **Class-conditional distributions** | **feature distributions by class (FR-4.4)** | categorical, **≤ 3 classes in one frame** | Overlaid density/histogram at 35% fill with a 2px stroke in the same slot. **This form is inherently multi-series and the caps still bind:** at ≤ 3 classes, one frame, slots 1–3. At 4+ classes it **facets — one small panel per class, each single-hue `series-1`, with a shared x-axis and a shared y-scale** so the panels are comparable. Facet cap 6, as for boundaries; above 6 the plot is not offered. |
| **Structure** | tree diagram | none | See § Components → *Decision-tree diagram*. Nodes on `background-paper` with `divider` borders and `chart-ink` text; split conditions in `chart-annotation`. Leaf nodes may take a `seq` fill on predicted value. Never rainbow the branches. |
| **Decision path** | **method-selection flowchart (FR-2.2)** | none — path vs. not-path | See § Components → *Method-selection flowchart*. Not a series form: the only distinction is traversed vs. untaken, carried by border weight, fill, dash pattern, and step badges as well as `series-1`. |
| **EDA** | histogram (numeric), **bar chart (categorical)**, boxplot, target distribution | nominal → one hue | All `series-1`. A histogram is one series; it does not need four colours. **Categorical bar chart:** sorted **frequency-descending**, horizontal bars so long category labels have room, **top 15 categories** with the tail folded into a single `{colors.series-other}` `#757575` bar labelled `Other (N categories)` — the primary legitimate use of `series-other` (the other is the multiclass tail fold in § Colors). **Correlation heatmap** is the exception and the only true diverging case — see § Components → *Correlation heatmap*. |
| **Pairwise** | **pairwise feature scatter coloured by target (FR-4.4)** | categorical, **cap 3** | Scatter rules apply in full: 3-slot cap, marker shape per class, 2px `#ffffff` ring, 60% opacity above 200 points. For regression targets the colour channel becomes the `seq` ramp on the target value with a ramp legend, not categorical slots. |

### Table-view form, per family

`View as table` is mandatory on every panel, but **what a table *is* differs by family**, and three families have no meaningful table. Specifying this per family is what keeps the mandate honest.

| Family | Table form |
|---|---|
| ROC, calibration, tuning curves, learning curve, train-vs-validation, shrinkage paths | The plotted series as columns, x as rows. Downsample to ≤ 100 rows and say so in the header. |
| Coefficients / importance | Feature × value, sorted as plotted. The full list, not the top-20 fold — this is where the other 480 live. |
| Confusion matrix, correlation heatmap, benchmark heatmap | The matrix itself, as a real `Table` with row and column headers. This is the *better* representation for all three, not a fallback. |
| Histogram, categorical bar, boxplot, target distribution | Bin / category × count, or the five-number summary for a boxplot. |
| Residual, predicted-vs-actual, pairwise scatter, class-conditional distributions | Summary statistics, **not the raw point cloud** — n, mean, SD, min/max, and the fit statistic. A 14,000-row table is not a text equivalent. |
| **Decision boundary** | **No meaningful table.** A 2-D prediction raster is not tabular data. Ships a **text summary** instead: the two features plotted, the class count, per-class point counts, and the training accuracy on the plotted projection. |
| **Tree diagram** | **No meaningful table.** Ships a **text summary**: an ordered list of the rendered split conditions with each node's sample count and predicted value, in traversal order, plus the truncation statement. |
| **Method-selection flowchart** | The traversed path as an **ordered list**: step number, question, the user's answer, and the branch not taken. |

### Mark specs (uniform across all ~29 charts)

- **Lines** 2px. Never thicker; never a glow, gradient, or shadow.
- **Dots / markers** ≥ 8px diameter, with a **2px `#ffffff` ring** anywhere marks overlap (scatter, decision boundary, support-vector overlay). Interactive marks get a ≥ 24px hit area — a visual floor, not a behavior; the hover model lives in `EXPERIENCE.md § Chart Behavior Contract`.
- **Bars** 4px radius on the value end only, square at the baseline; **2px surface gap** between adjacent bars and between stacked segments.
- **Heatmap cells** ≥ `{spacing.heatmap-cell-min}` 24px, 2px `#ffffff` gap. No cell borders — except the whole-matrix border on the correlation heatmap, for the reason given above.
- **Gridlines** 1px `{colors.chart-gridline}` `#e0e0e0`, horizontal only — vertical gridlines only where the x-axis is a real continuous scale (lambda, iteration). **Axis rule** 1px `{colors.chart-axis}` `#bdbdbd`. Both recessive: the marks are the content.
- **Scatter opacity** 60% above 200 points, 100% below. Above ~5,000 points, change form (hexbin or 2-D density) rather than piling up marks. `[ASSUMPTION — no density threshold exists upstream, but a 50 MB CSV can be very large.]`
- **Bar charts always start at zero.** Line charts on bounded metrics (accuracy, AUC, R²) run the full 0–1 unless the variation is genuinely under 0.05, in which case the zoom must be stated in the `chart-subtitle`.
- **Never a dual y-axis.** Two measures of different scale become two stacked plots sharing an x-axis, or get indexed to a common base. This product has tempting cases — training loss + accuracy by epoch is the worst — and the answer is always two plots.
- **Every truncation is disclosed in the `chart-subtitle`.** Top-20 coefficients, top-30 correlation features, top-15 categories, depth-capped trees, dropped confusion-matrix numbers, un-rendered boundary plots above 6 classes. A chart that quietly shows part of the data is the one failure mode this system cannot tolerate.

### Chart controls

Any control that filters or reconfigures a plot — the 2-D projection feature swap (FR-4.3), the "Add visualization" picker (FR-4.4) — sits in **one row above the plot grid**, not scattered per panel. Chart tooltips are MUI `Tooltip` at default elevation and `{rounded.sm}` 4px, containing the x value, a `series-N` swatch, the series name in `{colors.chart-ink-muted}`, and the value in `{typography.metric-value}` tabular. *Which charts get which tooltip form, crosshair vs. per-mark, click-to-isolate legends, and every other interaction rule: `EXPERIENCE.md § Chart Behavior Contract`.*

### Accessibility

- **Colour is never the sole carrier.** Every chart with ≥ 2 series has a legend, and at ≤ 4 series it is *also* direct-labelled. Train/validation splits by dash pattern. Boundary and pairwise classes by marker shape. Confusion-matrix and correlation cells carry their number within their stated caps. Status markers carry icon + label. Delta carries a glyph and a sign — and when tied, a word — and carries **no** colour signal in either direction, so it is not merely colour-plus-glyph, it is glyph-only. Method characteristics carry a word and a dot count. The flowchart path carries border weight, fill, dash, and a step badge.
- **CVD.** The 4-slot order was validated under protanopia and deuteranopia (Machado–Oliveira–Fernandes 2009, severity 1.0): worst adjacent CVD **ΔE 9.2** (`#eb6834`↔`#1baf7a`, deuteranopia; target ≥ 8) and worst adjacent normal-vision **ΔE 22.9** (`#1baf7a`↔`#eda100`; floor ≥ 15). `{colors.series-other}` `#757575` was validated against all four slots on the same basis, worst **ΔE 10.5**. The 3-slot all-pairs cap for scatter and boundary forms comes from that same validation and is not negotiable by taste.
- **Contrast.** `series-1` 4.42:1, `series-2` 3.20:1, and `series-other` 4.61:1 clear 3:1 on `#ffffff`. `series-3` (2.82:1) and `series-4` (2.17:1) do not — **any chart using slots 3 or 4 must ship visible direct labels or the table view.** Chart text sits at `#212121` (16.10:1) or `#666666` (5.74:1); 11px axis ticks stay at `#666666`, never lighter, never smaller.
- **Target size.** Every interactive chart cell is ≥ 24 × 24px (`{spacing.heatmap-cell-min}`); every interactive mark carries a ≥ 24px hit area.
- **Texture** (a 45° / 135° line fill, tone-on-tone) is available for filled regions under `forced-colors`, print, or an explicit accessibility setting. Never decorative, never on by default. `[ASSUMPTION — no accessibility-settings surface is specified in the PRD; treat this as a print / forced-colors provision only.]`
- *The `role`/`aria` contract, the announcement model, and focus behavior live in `EXPERIENCE.md § Accessibility Floor`.*

### Load-bearing accessibility specifications

This product will be built by one person who is also writing a thesis, and some of the specifications above are expensive. **Several of them are the only thing standing between this file and a false accessibility claim.** They are listed here so that cutting one is a *visible decision* rather than a silent regression.

**Rule: cutting any row below requires recording the cut in `.memlog.md` and deleting the corresponding claim from `EXPERIENCE.md § Accessibility Floor` and from the thesis.** A cut with the claim left standing is the failure mode this table exists to prevent.

| # | Visual specification | The claim it carries | What becomes false if cut | Cheapest survivable substitute |
|---|---|---|---|---|
| 1 | **Direct labels on marks whenever `series-3` / `series-4` are used** | WCAG 1.4.11 for the two sub-3:1 slots | The palette's ⚠ WARN becomes an unmitigated 1.4.11 failure on every 3- and 4-series chart | **None.** If direct labels go, the cap drops to 2 series per frame and the 4-method overlay claim goes with it. Cut this last. |
| 2 | **`View as table` on every panel** | "Every chart has a text equivalent"; the screen-reader fallback; the second relief channel for slots 3/4 | The text-equivalent claim, and the WCAG 2.2 AA claim that rests on it | `role="img"` + a descriptive `aria-label` carrying the chart's headline value on **every** panel, plus tables on only the families where a table is the *better* form (confusion matrix, correlation, benchmark, coefficients, EDA). Rows 1, 3, 4, 5 must then all survive. |
| 3 | **Marker shape per class** (boundaries, pairwise, class-conditional) | WCAG 1.4.1 use of colour | Multiclass boundary and pairwise plots become colour-only | Facet to one class per panel. Cheaper than it sounds; already the ≥4-class rule. |
| 4 | **Dash pattern on the train/validation pair** | WCAG 1.4.1 | Every train-vs-validation chart becomes colour-only | Two stacked plots sharing an x-axis. |
| 5 | **In-cell numbers** in confusion and correlation matrices (within their caps) | 1.4.1, and legibility of the near-zero band where `div-mid` is 1.11:1 | Cell values become hover-only — unreachable by keyboard and screen reader | Row 2's table view. Rows 2 and 5 **cannot both be cut**. |
| 6 | **`✓` / `✗` glyphs** on benchmark agreement | 1.4.1 | Agreement becomes a colour difference on top of a sequential ramp — unreadable under CVD | None. It is one glyph per cell; it is the cheapest row here. |
| 7 | **Delta glyph `▲ ▼ =` + the word `tied`** | 1.4.1 | Delta direction loses its **only** carrier. Better and worse are the same ink by decision, so there is no colour fallback to degrade to — the glyph is not a redundant channel here, it is the channel | **None, and this row is stricter than it looks.** The sign of the number is the only thing left; `tied` cannot be expressed as a number at all. Restoring a green/red fallback is not a permitted substitute — see § Colors. |
| 8 | **`InfoOutlined` 16px at `{colors.text-secondary}`** on disabled chips | 1.4.11 non-text contrast | Disabled state is carried by a 2.68:1 label colour alone | None. It is a colour prop and a size prop. |
| 9 | **Disabled-reason text at `#666666`, not `text.disabled`** | WCAG 1.4.3 | The reason — the entire point of disabled-with-reason — drops to 2.68:1 | None. It is one token. |
| 10 | **Status icon + label always paired** | 1.4.1, and mitigation for `status-warning` 1.79:1 / `status-serious` 2.57:1 | Two of the four status colours become sub-3:1 signals with no carrier | None. |
| 11 | **Word + dot count in the Method characteristics table** | 1.4.1 for the only evidence artifact advice-only mode ships | The five qualitative axes become colour or position alone | The word alone. Drop the dots, keep the word — never the reverse. |
| 12 | **Reflow to a single column below 800px, in-panel chart scrolling only** | WCAG 1.4.4 zoom + 1.4.10 reflow, and EXPERIENCE.md's 200%-zoom statement | The 200%-zoom claim, and the product acquires page-level horizontal scroll | None. This is a media query and one `overflow-x`. |
| 13 | **24 × 24px minimum interactive cell** (benchmark, correlation) | WCAG 2.5.8 target size | ~1,600 benchmark cells become sub-target-size pointer targets | None; it is a min-width. |

Rows 6–9 and 12–13 are each a single token or property and should never be cut. Rows 1–5 and 11 are real work, and rows 2 and 5 are explicitly coupled.

### Chart Do's and Don'ts

*These are the **chart-layer** rules only — palette caps, mark specs, truncation, table views. Token, layout, elevation, shape, and state rules live in the terminal § **Do's and Don'ts**. Nothing is stated in both.*

| Do | Don't |
|---|---|
| Assign `series-1` to the recommended method for the whole session | Re-assign colours when the results ranking reshuffles the methods |
| Give a newly selected method the **lowest free slot** | Leave a re-selected method with no slot, or repaint methods the user didn't touch |
| Cap scatter / decision-boundary / pairwise / small-multiple forms at **3** series | Add a 4th hue to a boundary plot — yellow↔orange fails the normal-vision floor at ΔE 13.7 |
| One hue for coefficient and importance bars, top 20 with a stated fold | Colour bars by their own value; or render 500 bars in a 4:3 panel |
| Diverging blue↔red with a **gray** midpoint for correlation, capped at 30 features | A rainbow ramp, any hue at the midpoint, or a 500 × 500 matrix |
| State every truncation in the `chart-subtitle` | Silently show part of the data |
| Two stacked plots sharing an x-axis for two different scales | A dual y-axis, ever |
| Direct-label or ship the table view whenever `series-3` / `series-4` are used | Ship a sub-3:1 fill with neither |
| Split train/validation by **dash**, classes by **marker shape** | Rely on hue alone for either |
| Print the number inside confusion and correlation cells, within their caps | Make the reader estimate a value from a colour ramp — or print an 11px number in a 0.6px cell |
| Keep reference lines (y = x, chance diagonal, perfect calibration) neutral dashed gray | Give a reference line a series colour — it isn't a series |
| Cap tree depth and mark the cut with a `⋯ N more splits` node | Build a pan/zoom canvas, or let a tree overflow its panel |
| 2px lines, ≥ 8px markers, ≥ 24px interactive cells, recessive 1px gridlines | Gradients, glows, 3-D, shadows on marks, area fill under every line, text below 11px |

## Do's and Don'ts

*This file carries **two** rule tables and a reader looking for a rule must know which one to open. This one holds the **non-chart** rules — tokens, layout, elevation, shape, state treatments. The chart-layer rules (palette caps, mark specs, truncation, table views) live in § Data Visualization → **Chart Do's and Don'ts**. Nothing is stated in both.*

| Do | Don't |
|---|---|
| Keep MUI defaults for `palette.primary`, `typography`, `shape.borderRadius`, `spacing()` | Invent a parallel token system beside MUI's |
| Use MUI components unrestyled (`Button`, `Select`, `Alert`, `Table`, `Accordion`) | Spend design effort theming form controls instead of charts |
| Separate with `{colors.divider}` hairlines and whitespace | Reach for elevation as a hierarchy device — only the sticky summary bar and overlays float |
| Elevation 0 + 1px border on every plot panel, card, **and the top bar** | Give the top bar a shadow, or an elevation-on-scroll behavior |
| 8px radius on plot panels, the metrics row, and result cards; 4px everywhere else | A third radius step, or pills on anything but `Chip`, the meter track, and rating dots |
| Derive breakpoints from `4 × 320 + 3 × 24 + 64 = 1416` and publish the arithmetic | Assert a column count the panel floor cannot support |
| Reflow to a single column below 800px | Declare any viewport "unsupported" — it contradicts the 200%-zoom claim |
| Scroll a too-wide chart **inside its own panel** | Let the page scroll horizontally, at any width or zoom |
| Align **only** the shared metrics row across comparison columns | Attempt cross-column plot row alignment — FR-4.2 gives every method a different plot set |
| Let comparison columns have different heights | Stretch, pad, or reorder a column to fake alignment |
| Render the disabled-method **reason** at `#666666` (5.74:1) and its icon at 16px / `#666666` | Let the load-bearing disabled icon inherit `text.disabled` at 2.68:1 |
| Encode the five qualitative axes as **word + dot count** | Encode ordinal quality with the reserved status palette, green/amber/red |
| Dim stale results with opacity **0.55 + saturate(0.5)** together, plus the banner | Hide, clear, or destroy stale results — old answers stay readable |
| Show the fit score as a one-hue meter **plus** the numeral | Threshold-colour the fit score green/amber/red — that borrows the reserved status palette |
| Render delta % in **neutral ink both ways**, with `▲` / `▼` / `= tied` carrying direction | Colour delta green-up / red-down — it primes the reader against a result the thesis is trying to measure |
| Tabular figures on every metric in the shared metrics row | Proportional figures in aligned numeric columns |
| Let plots wrap to their own row rather than shrink below the 320px **panel** floor | Squash a panel below `{spacing.plot-min-width}` at ≥800px, or distort the 1:1 aspect of a boundary / heatmap / confusion matrix |
| Keep chart text in ink tokens with a colour swatch beside it | Set legend or label text in the series colour |
| Treat the load-bearing a11y table as a cut ledger: cut a row, delete the claim | Cut a mitigation and leave the WCAG claim standing in EXPERIENCE.md or the thesis |
| Keep the palette light-surface only, as validated | Add dark mode with a filter flip, a `prefers-color-scheme` query, or `palette.mode: 'dark'` — every gate in this file fails |
| Add a visual idea only when a chart genuinely can't be read without it | Add a brand system — there is no brand, and "simple UI" is a constraint, not a preference |
| Specify behavior in `EXPERIENCE.md` and look in `DESIGN.md` | Restate a behavioral rule here — two sources of truth is how the spines drift |
