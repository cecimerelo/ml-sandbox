---
title: Adversarial Review — TFM UX Spines
reviewer: Cynical Adversarial Review
date: 2026-08-08
targets:
  - ./DESIGN.md
  - ./EXPERIENCE.md
context:
  - ./.memlog.md
  - ../../prds/prd-TFM-2026-07-26/prd.md
  - ../../prds/prd-TFM-2026-07-26/addendum.md
---

# Adversarial Review — TFM UX Spines

## Verdict

Two unusually disciplined documents with a real spine, a genuinely validated chart
palette, and a coherent behavioral posture. They are also **written as if a team
will build them**, and they contain a small number of defects that are not stylistic:
a core comparison layout that cannot be built as specified, a loading estimate that
understates reality by 5–25×, a layout that violates its own hard minimum in the most
common viewport range, and — most seriously — a set of UI decisions that will
contaminate the thesis's own research metrics.

The quality of the writing is itself a risk. Because the prose is confident and
mandate-shaped ("mandatory, not optional", "a plot panel that breaks any of these is
a bug"), it gives no signal about what to cut. A solo student will cut things anyway.
The spines do not say which cuts are survivable, and several of the load-bearing
accessibility claims collapse quietly when the obvious cut is made.

Ranked findings follow. Severity bands: **BLOCKER** (would produce a broken or
indefensible artifact), **MAJOR** (will cost real rework or draw committee fire),
**MEDIUM**, **MINOR**.

---

## BLOCKER

### B1. The UI systematically biases the thesis's own success metrics

**What's wrong.** The PRD's user-satisfaction metric is *"Recommendation acceptance
rate: % of sessions where the user ran the recommended method"* (FR-7.3, Success
Metrics), and the counter-metrics are *recommendation diversity* and *the most complex
method must not be systematically over-recommended*. The UX as specified makes all
three unmeasurable or biased:

1. **The metric is degenerate by construction.** FR-8.4 auto-trains up to 5 methods
   ordered by fit score. The recommended method is by definition rank 1, so it is
   *always* trained. "Whether the user ran the recommended method" is therefore
   always true. The metric measures nothing. EXPERIENCE.md's Coverage Check calls
   this "Not a gap" (closure note 2) — it is the gap.
2. **The selector is a funnel.** The locked "3 promoted + Show all" decision means
   3 of ~22 methods are one-click chips and 18 are behind an `Accordion`. Which
   methods a user runs is therefore a function of the UI's promotion rule, not of
   user intent. "Methods run by user" (FR-7.3) is a measurement of the widget.
3. **Every remaining channel anchors toward the recommendation.** `series-1` is
   permanently the recommended method; the reference column is leftmost; deltas are
   green-▲/red-▼ *relative to the recommendation*; `Show all methods` sorts by fit
   score descending inside every group. DESIGN.md's own `[ASSUMPTION]` on the delta
   tokens (line 247) notices the green/red framing problem and then understates it as
   a color question. It is a measurement-validity question.

**Why it matters.** FR-6.4 makes benchmark evaluation "a formal secondary research
objective". A tutor or committee that spots the acceptance-rate tautology will
question the whole evaluation section, and the fix is not a UI tweak — it is a change
to what gets logged.

**What I'd do instead.** (a) Redefine the behavioral metric to something the UI can
actually vary: e.g. *"did the user add any non-promoted method via Show all"*, or
*"did the user's final comparison ranking put the recommended method first"*. (b) Log
the promotion set and the selector path alongside the chosen methods so the funnel is
a controllable covariate, not a confound. (c) Neutralize the delta framing (the
DESIGN.md assumption's own fallback: muted ink, glyph carries direction). (d) State
explicitly, in the thesis, that user-side metrics are observational and
interface-conditioned — do not present them as unbiased.

---

### B2. "Row-aligned plots across comparison columns" is impossible given FR-4.2

**What's wrong.** DESIGN.md § Layout: *"Comparison mode is column-per-method … with
**row-aligned plots** — the same plot type sits at the same vertical position across
all columns."* EXPERIENCE.md repeats it in the Comparison table row.

FR-4.2 gives every method a **different** fixed plot set. Compare Logistic Regression
(ROC · confusion matrix · coefficient plot) against Decision Tree (tree diagram ·
feature importance) against Ridge (shrinkage path · CV error vs lambda). There is no
shared plot type across those three, so no row can be aligned. In the general
4-method case the intersection is frequently empty.

It gets worse: DESIGN.md forces boundary / heatmap / confusion-matrix panels to `1/1`
while everything else is `4/3`. Even where a row *is* type-aligned, panel heights
differ across columns, so rows drift vertically after the first divergence.

**Why it matters.** This is the core layout of FR-5's headline feature and the climax
of Flow 4. It is not a detail — it is the thing the comparison page *is*. As written,
a developer reaches this and stops.

**What I'd do instead.** Pick one and specify it: (a) **Aligned-common + tail** —
render the intersection of plot types (in practice: confusion matrix or residual
plot, plus the shared FR-4.4 additions) as aligned rows at the top, then each column's
method-specific plots below in a ragged tail, each labelled. (b) **Metric row only** —
align on the numeric comparison table (CV score, RMSE/accuracy) and let plots be a
per-method stack with no alignment claim. (c) Normalize all comparison-mode panels to
a single aspect and accept the geometric distortion warning for boundaries. Option (a)
is the honest one; either way, delete the unqualified "row-aligned" sentence from both
spines.

---

### B3. The loading estimate understates the wait by 5–25×

**What's wrong.** EXPERIENCE.md, *Loading — training*: the estimate line is
*"derived from the tiered timeout band"* and reads `Training up to 5 methods. Usually
under a minute for a dataset this size.` (< 500 rows) / `usually 1–2 minutes` (500–10k)
/ `this can take up to 5 minutes` (> 10k).

Those numbers are the **per-method** timeouts from FR-8.4 (60s / 120s / 300s),
presented as **whole-run** estimates for *up to 5 methods*. The worst case is:

| Tier | Per-method timeout | Stated estimate | Actual worst case (5 methods, sequential) |
|---|---|---|---|
| < 500 rows | 60s | "under a minute" | 5 min |
| 500–10k | 120s | "1–2 minutes" | 10 min |
| > 10k | 300s | "up to 5 minutes" | **25 min** |

Even with early halt at 3 methods, the > 10k tier is 15 minutes against a stated
"up to 5". Flow 3 has Priya "watching `2 of 5… 4 of 5…`" under a 5-minute banner
while the spec permits 20+ minutes of the same screen.

**Why it matters.** NFR-1 requires "a loading indicator with estimated time". An
estimate that is wrong by an order of magnitude in the direction of *longer* is worse
than no estimate — it is the state where users reload the page and lose everything
(see M5). It also breaks Flow 4's projector demo, where the professor has fourteen
minutes.

**What I'd do instead.** Either (a) state the *ceiling* honestly (`Up to N methods ·
worst case ~X minutes`) and lean on the per-method streaming to make the wait feel
progressive, or (b) if methods train in parallel, say so and derive the estimate from
the per-method timeout plus a concurrency factor. Also resolve the coupled question
this exposes: **early halt (FR-8.4) is only possible if training is sequential, and
per-method streaming progress is only satisfying if it is parallel.** The spines
assume both and never reconcile them. Pick: sequential with early halt (accept the
long tail), or parallel with no early halt (and then delete the early-halt state
entirely).

---

## MAJOR

### M1. The layout violates its own 320px floor in the 1200–1440px range

**What's wrong.** DESIGN.md sets `content-max` 1440, `page-margin` 32 (both sides),
`plot-gap` 24 (also the plot panel's internal padding), and `plot-min-width` **320px**
as a *hard floor* — "a plot that cannot get 320px does not shrink, it wraps to its own
row." It then asserts 1440 "lets four comparison columns sit at ~330px each, above the
320px plot minimum," and that comparison drops to 2×2 only *below 1200px*.

Do the arithmetic:

- At the 1440 max: `1440 − 64 margins − 72 gaps = 1304 / 4 = 326px` per **panel**.
  Minus the panel's own 24px padding on each side → **278px of actual plot**. Below
  the floor.
- At a 1250px viewport (fully inside the "4 columns" range):
  `1250 − 64 − 72 = 1114 / 4 = 278px` per panel → **230px of plot**. Far below.

So across the entire 1200–1440 range the spec simultaneously mandates 4 columns and a
320px plot minimum. They are incompatible, and by the spec's own rule every panel
should wrap to its own row — which destroys the column-per-method comparison.

**Why it matters.** The ambiguity ("is 320 the panel or the plot?") plus the wrong
arithmetic means the developer will either silently shrink below the floor (breaking
the readability premise the whole chart system rests on) or wrap everything (breaking
comparison). Both are worse than a corrected number.

**What I'd do instead.** Define `plot-min-width` unambiguously as the **panel** width,
raise the 4-column breakpoint to `4 × 320 + 3 × 24 + 64 = 1416px`, and drop to 2×2
below that. Or reduce comparison-mode panel padding to `spacing(1)` and re-derive.
Either way, publish the arithmetic in the spec so it can be checked.

---

### M2. The accessibility story is load-bearing on the first thing that will be cut

**What's wrong.** `View as table` is doing an enormous amount of work in both spines:

- It is the **mandated relief channel** for `series-3` (2.82:1) and `series-4`
  (2.17:1), which fail the 3:1 mark-contrast floor. DESIGN.md: "Ship a sub-3:1 fill
  with neither [direct labels nor table view]" is listed as a Don't.
- It is the **screen-reader fallback**: "Every chart has a text equivalent."
- It is **mandatory on all ~25 panels**, per EXPERIENCE.md's Chart Behavior Contract.

It is also, for a solo student with a backend, a benchmark study, and a thesis to
write, the single most obviously droppable item in the document — ~25 bespoke
tabular serializations, one per chart form, each of which must not "change panel
height enough to reflow the grid above it."

And it is **underspecified for the charts where it is hardest**: what is the table for
a decision boundary (a 2-D prediction raster)? For a tree diagram? For a correlation
heatmap at 500 features (250,000 cells)? For a shrinkage path (many × many)? Neither
spine says. The easy cases (ROC, bars) are the ones you don't need it for.

**Why it matters.** When it's cut, the palette's WARN becomes an unmitigated
WCAG 1.4.11 failure and the WCAG 2.2 AA claim in EXPERIENCE.md § Accessibility Floor
becomes false. The thesis will contain an accessibility claim the artifact doesn't
support — exactly the kind of unbacked assertion a committee picks at.

**What I'd do instead.** (a) Specify the table representation *per plot family*, not
globally; explicitly declare tree diagram, decision boundary, and >50-feature
correlation heatmap as **"no meaningful table — ships a text summary instead"** and
say what that summary contains. (b) Make direct labelling (not the table) the primary
relief for slots 3/4, since it's cheap and lives in the chart code you're already
writing. (c) Downgrade the global claim to what will actually ship: "every chart
carries `role="img"` + a descriptive `aria-label`; tabular data views on the N chart
families where a table is meaningful."

---

### M3. The education layer is specified as an aspiration, not as copy

**What's wrong.** The explanation layer is the pedagogical heart of the thesis and it
has: a voice table with 10 do/don't pairs, four placement rules, three hard
constraints — and **zero complete specimens** of the highest-volume text in the
product. Flow 1 step 5 paraphrases an explanation rather than quoting it. Not one
form-question explanation and not one `chart-subtitle` appears verbatim anywhere.

The volume is not small. Counting from the spec:

- 11 form questions × 1 explanation each (both shapes) — plus the Shape A/Shape B
  variants where the question differs.
- ~25 `chart-subtitle` lines, each of which must explain *how to read* an unfamiliar
  chart in one 12px line.
- Disabled-with-reason strings: ~22 in-scope methods × 3 prediction types (regression
  / binary / multiclass) — up to ~66 strings, plus the cap message, plus the FR-4.4
  library items.

That is 100+ pre-authored, plain-language, citation-free, pedagogically defensible
strings, and the spine that says they are "static and pre-authored" never says where
they live, who reviews them, or what the template is.

**The "citation-free" constraint has a real failure mode the spec doesn't handle.**
EXPERIENCE.md requires: *"Any term of art used in an explanation is defined in that
same explanation, or is not used"* AND *"2–3 sentences maximum."* The document's own
example already breaks this: *"Flexible methods bend to fit your data. That helps when
the pattern is complex, and hurts when there isn't much data to learn from."* —
"flexible" is a term of art (it's the ISLR flexibility axis), it is not defined, and
the sentence quietly asserts the bias-variance tradeoff without naming it. That
explanation is charming and *approximately* wrong: flexibility hurts with small n
**relative to the true function's complexity**, not absolutely. This is the exact
vagueness-becomes-wrong trap the constraint invites.

**Why it matters.** A supervisor will ask "how do you know these explanations are
correct?" The spec's answer is currently "they're paraphrases." Banning citations
*in the UI* (FR-2.3) does not remove the obligation to have provenance *for the
thesis*.

**What I'd do instead.** (a) Write and include in this spec a **template plus three
worked specimens**: one form-question explanation, one chart subtitle, one disabled
reason — verbatim, at final length. If you cannot write three, the strategy isn't
specified. (b) Maintain a **non-UI copy→ISLR-section traceability table** as a thesis
appendix. The UI stays citation-free; the thesis proves the pedagogy is grounded.
That single artifact converts your biggest defense risk into a strength. (c) Add a
constraint the spec is missing: an explanation must not assert a claim stronger than
the engine's rule that consumes it.

---

### M4. The un-stale-without-re-running behavior cannot work as specified

**What's wrong.** EXPERIENCE.md's *Un-stale without re-running* state ("the user
reverts every changed answer to the values the results were computed from → the dim
lifts, no round-trip") is Flow 3's **climax** (step 8). It is tagged `[ASSUMPTION]`,
but the tag frames it as a product choice; the problem is that it is not implementable
against the rest of the spec.

Concrete failures:

1. **The dataset-removal path can never un-stale.** Stale fires on "dataset removal".
   On removal, "fields 2–7 carry over as manual bands, mapped from the detected
   values (8,412 rows → `500–10k`)". That mapping is **lossy**. The results were
   computed from `8412`; the form now holds `500–10k`. No sequence of user actions
   short of re-uploading a byte-identical file restores equality — and the spec never
   defines file identity. So Flow 3's own failure branch (Priya removes the dataset)
   enters a state with no exit but a re-run, which the spine implies is avoidable.
2. **The column-name toggle stales results it doesn't affect.** Stale fires on "any
   form answer changes (**including toggles**)". The column-name toggle is explicitly
   *not* an engine input — it only sources interaction-pair suggestions, and
   "toggling never triggers a round-trip." Flipping a privacy switch therefore dims
   four minutes of plots for no reason. That is the opposite of the non-destructive
   posture.
3. **Equality is undefined for the compound fields.** Interaction pairs are a *set*
   from an `Autocomplete multiple`. Is `[(a,b),(c,d)]` equal to `[(c,d),(a,b)]`? Is
   `(a,b)` equal to `(b,a)`? Nothing says. Get this wrong and un-stale never fires,
   which reads to the user as a bug.
4. **The snapshot must include things the spec never enumerates**: the feature-swap
   selections (which trigger their own partial re-fetch), which methods were trained,
   the early-halt outcome, and any `Add visualization` panels.

**Why it matters.** This is a nice-to-have dressed as an emotional peak. If it's the
first thing cut (it should be a candidate), Flow 3 loses its ending and the document
doesn't notice.

**What I'd do instead.** Specify the snapshot explicitly: **the set of fields that are
engine inputs** (FR-2.1's list), canonicalized — bands not raw values, pair sets
order- and direction-normalized, dataset identified by a content hash computed at
upload. Exclude the column-name toggle and the pair-suggestion source from the
staleness set entirely. Declare removal-of-dataset a **one-way** stale (no un-stale
path) and say so in the flow. If that's too much, cut un-stale and rewrite Flow 3's
climax around the dim-and-survive behavior alone, which is already the good part.

---

### M5. Real datasets break this UI in ways neither spine covers

NFR-2 permits 500 features and 50MB. Neither spine bounds anything downstream of that.

| Input | What the spec produces | What actually happens |
|---|---|---|
| **500 features** | FR-3.3 correlation heatmap "between features", with `r` printed in each cell at 11px, 2px gaps | 250,000 cells. In a 320px panel each cell is 0.64px. The annotation rule is physically impossible, and `div-mid` `#f0efec` at **1.11:1 on `#ffffff`** means the near-zero region — which is most of a 500-feature matrix — is invisible against the surface. |
| **500 features** | FR-3.3 "distribution plots per feature" | 500 plot panels inside a single `Accordion`. Expanding EDA hangs the tab. |
| **500 features** | Coefficient plot / feature importance, "all bars `series-1`, sorted by magnitude" | 500 bars in a 4:3 panel. |
| **100-class multiclass** | "A decision boundary with more than 3 classes … facets one-vs-rest — one small-multiple panel per class. The facet decision is made by the system … **not offered as a user choice**" | 100 panels, automatically, with no cap. Also a 100×100 confusion matrix with a number in every cell. |
| **Target with 1 unique value** | Not covered. "Detection failed entirely" only covers *unresolvable type* | Detector says "multiclass, 1 class". Training produces degenerate models; ROC is undefined; class balance is meaningless. Silent nonsense. |
| **Target = an ID column** (n unique values ≈ n rows) | Detector says multiclass with 8,000 classes | See above, ×80. |
| **All-categorical data** | Feature types "categorical" is a supported answer | Correlation heatmap (numeric-only), residual plots, and scatter forms have nothing to plot. No spec for what the EDA block renders. |
| **50MB CSV** | Dropzone "on accept collapses to a filename row"; feature count "checked server-side on the header row" | No upload-in-flight state, no progress, no cancel, and an ambiguity about whether 50MB crosses the wire before the header check. |
| **Deep decision tree** | "Tree diagram" with node boxes and split conditions | An unpruned tree on 14,000 rows has thousands of nodes. No depth cap, no pan/zoom, no `1/1` rule, no fallback. |

**What I'd do instead.** Add a **"Scale Guards"** subsection to EXPERIENCE.md § State
Patterns with explicit, stated-in-UI truncations:
- Correlation heatmap: top-K features by variance (K ≈ 30), annotation only at K ≤ 20,
  caption says which K and why.
- Distributions: paginated or top-K, with a feature picker.
- Coefficients/importance: top-20 + "and 480 more" fold.
- Multiclass: hard cap facets at ~6; above that, drop boundary plots entirely and say
  so in the subtitle. Cap confusion-matrix annotation at ~10 classes.
- Target validity: add a rejection/warning state for `nunique == 1` and for
  `nunique / n_rows > 0.5` ("this looks like an ID column, not a target").
- Tree diagram: depth cap with "showing the first N levels".
- Upload: add an in-flight state with progress and cancel.

Every one of these is also a *good thesis result to report* — "we found the following
scale limits and here is how the interface degrades" is a legitimate findings section.

---

### M6. Scope realism — the spec has no cut order, and the mandates fight the student

**What's wrong.** The spines are written entirely in hard rules. "Mandatory, not
optional." "A plot panel that breaks any of these is a bug, not a variant." "Not
negotiable by taste." There is no tiering, no MVP subset, and no statement of what
degrades gracefully. For a team, this is good discipline. For one student who is also
building a backend, running an OpenML-CC18 + UCI benchmark study, implementing an
AMLBID comparison, and writing a thesis, it is a document that will be silently
violated rather than deliberately reduced.

The items most likely to be cut, and what breaks when they are:

| Likely cut | What silently breaks |
|---|---|
| `View as table` on all panels | The sub-3:1 palette mitigation, the "every chart has a text equivalent" claim, the WCAG 2.2 AA claim (see M2) |
| Per-method streaming progress | The whole *Loading — training* state, the `N of 5` line, three `aria-live` announcements, the "a method's panels appear together" rule, and the Flow 1 + Flow 3 climaxes |
| Un-stale without re-running | Flow 3's climax (see M4) |
| ~25 `chart-subtitle` lines | The Explanation Layer's third placement — i.e. one quarter of the pedagogy (see M3) |
| Report-an-error dialog | Flow 2's failure branch and half of FR-6.2 |
| BART / GAM / splines plots | FR-4.2 rows for methods whose Python ecosystem barely supports them (no BART in sklearn; posterior credible intervals and variable inclusion proportions are bespoke) |

The chart count is also understated. DESIGN.md says "~20 method-specific plots, 4 EDA
plots, and a benchmark heatmap." FR-4.4's closed library adds **four more** chart types
(learning curve, calibration curve, feature distributions by class, pairwise feature
scatter) — and DESIGN.md's *Slot assignment by plot family* table never assigns rules
to them. "Feature distributions by class" is a per-class overlay form, i.e. it needs
>3 series for any multiclass problem, which the 3-slot scatter cap forbids and no rule
resolves.

**What I'd do instead.** Add a short **Build Tiers** section to EXPERIENCE.md:
- *Tier 1 (thesis-defensible minimum)*: form + inline explanations + recommendation
  panel + advice-only mode + EDA + the recommended method's plots + benchmark heatmap.
- *Tier 2*: comparison mode, per-method streaming, timeout/early-halt disclosure.
- *Tier 3*: un-stale, `Add visualization`, feature swap, per-panel table views.

And for each Tier-2/3 item, one line: *"if cut, the following claim must be removed
from the spec and the thesis."* That sentence is what protects you at the defense.

---

### M7. Privacy: column names end up in the permanent record, contradicting the toggle's promise

**What's wrong.** Three statements cannot all be true:

1. EXPERIENCE.md § Column-name opt-in: the toggle's explanation "states plainly that
   column names — not data values — are read to suggest interactions, and **that this
   is the only thing column names are used for**."
2. EXPERIENCE.md § Form, field 11: the user's confirmed interaction pairs are *"named
   pairs … additional signal"* consumed alongside the three-option answer.
3. FR-7.3: the backend **permanently stores** decision drivers including *"feature
   interactions"*.

If the named pairs are part of the stored decision-driver record, then the user's
actual column names (`salary`, `patient_id`, `diagnosis_code`) are permanently stored,
the toggle's explanation is false, and "anonymized" is doing work it can't do —
column names from a private dataset are frequently identifying of the dataset and
sometimes of its subject domain. FR-5.5's free-text feedback field has the same
exposure.

**Why it matters.** This is a Spanish master's thesis; GDPR is in scope and an ethics
question at the defense is plausible. EXPERIENCE.md also hard-commits to *"never a
consent gate — the product does not block on it"* for a system that permanently
stores user-derived data. That is a defensible choice for non-personal data and a
weak one if column names are in the record.

**What I'd do instead.** Decide explicitly and write it down: either (a) **store only
the boolean/three-option interaction answer and a count of named pairs, never the
names** — then the toggle's promise is true and the consent-free posture is
defensible; or (b) if the names are needed for the research, hash them, say so in the
notice, and stop calling the record "anonymized" without qualification. Also specify
what happens to FR-5.5 free text (it is user-authored and cannot be assumed clean).

---

## MEDIUM

### D1. Cross-spine contradiction: `disabled` attribute vs. `aria-disabled`

DESIGN.md § Method chip: *"**Wrap the chip in a `<span>`** so the tooltip still fires
on a disabled element; set `aria-disabled`."* The span-wrap is the standard MUI
workaround for the **real `disabled` attribute** — you don't need it with
`aria-disabled`.

EXPERIENCE.md, twice: *"Disabled chips are **still focusable** (`aria-disabled`, **not
the `disabled` attribute**)."*

These specify different DOM. Following DESIGN.md produces a non-focusable chip whose
reason is unreachable by keyboard — which defeats the entire "nothing is hidden"
posture that made disabled-with-reason a decision in the first place. **Fix:**
`aria-disabled` + `tabindex="0"` + `aria-describedby`, no span wrap, no `disabled`
attribute; delete the span sentence from DESIGN.md.

### D2. `role="img"` on the chart container removes the `View as table` toggle from the a11y tree

EXPERIENCE.md § Accessibility Floor: *"Each chart container carries `role="img"` with
an `aria-label`."* DESIGN.md § Plot panel puts the `View as table` text button
top-right, *inside* the panel anatomy.

`role="img"` makes the entire subtree presentational. If the toggle sits inside the
element carrying `role="img"`, screen-reader users cannot reach the fallback that the
spec designates as their fallback. **Fix:** `role="img"` goes on the SVG/canvas only;
title, subtitle, legend, footnote, and the toggle live outside it as normal content.

### D3. The disabled-chip icon — the mandated non-color carrier — fails contrast

DESIGN.md: *"An `InfoOutlined` **12px** icon is appended inside the chip. **This is the
non-colour carrier**: a chip is disabled because it has the icon, not because it looks
pale."* The icon's color is never specified; the surrounding `method-chip-disabled`
tokens set `foreground: {colors.text-disabled}` `#9e9e9e` = **2.68:1**, and MUI icons
inherit label color by default.

So the graphic that is explicitly load-bearing for non-color state sits at 2.68:1,
below WCAG 1.4.11's 3:1 for meaningful non-text content, at 12px. The spec is careful
about exactly this everywhere else (it insists the *reason text* be `#666666`, not
`text.disabled`) and then misses it on the icon. **Fix:** set the icon explicitly to
`{colors.text-secondary}` `#666666` (5.74:1) and bump to 16px.

### D4. DESIGN.md encodes delta % two different ways

§ Diverging: *"Used for: … and the **delta %** column against the recommended method."*
§ Delta badge: three discrete tokens (`#006300` / `#d03b3b` / `#666666`), *"Text only.
No pill, no fill, no background."*

A continuous diverging ramp and a three-state text color are mutually exclusive
encodings of the same quantity in the same file. **Fix:** delete delta % from the
diverging ramp's use list — the badge is the right answer (it carries a glyph, which
the ramp cannot).

### D5. "Hover reveals information, never actions" vs. the benchmark cell tooltip

EXPERIENCE.md § Interaction Primitives states the rule as a hard ban. Both spines then
put an **action** in a hover tooltip:

- DESIGN.md § Benchmark heatmap: *"Cell hover shows dataset, method, score, and the
  **'Report an error' affordance**."*
- EXPERIENCE.md § Component Patterns: *"Hover reveals dataset, method, score,
  agree/disagree marker, and the row's **`Report an error` affordance**."*

Beyond the contradiction, this is **unbuildable with MUI `Tooltip`**: tooltip content
is not pointer-reachable (moving toward it dismisses the tooltip), and it is not in the
tab order. **Fix:** tooltip carries data only; `Report an error` lives as a persistent
per-row button in a leftmost/rightmost row-header column, and `Enter` on the roving
grid cursor opens it (which the keyboard spec already says).

### D6. Early halt makes a statistical claim the design can't support

The copy: *"We stopped after 3 methods — their scores were too close to separate, so
**training more wouldn't have told you anything new**."*

That inference does not follow. The top 3 being within 1 SD of each other says nothing
about whether methods 4 and 5 would beat them — FR-8.4 orders candidates by *heuristic
fit score*, and the entire premise of FR-6.4's evaluation is that the heuristic is
sometimes wrong. The interface is asserting a conclusion the thesis is explicitly
testing.

This is a copy line a committee member could quote back. **Fix:** make the copy
describe what happened, not what it implies: *"We stopped after 3 methods — the top
three scored within one standard deviation of each other, so we didn't train the rest.
You can still add them below."* The second sentence is already true in the spec
(remaining methods stay selectable) and it converts an unjustified claim into a
transparent one.

### D7. The 200% zoom claim contradicts the layout spec

EXPERIENCE.md § Accessibility Floor: *"The page works at 200% browser zoom — the
desktop-first layout reflows per `DESIGN.md § Layout & Spacing` rather than requiring
horizontal scroll. `[ASSUMPTION — 200% is the WCAG 1.4.4 requirement]`."*

DESIGN.md § Layout: *"below 900px the layout is **unsupported** — desktop-first, no
mobile in v1."*

200% zoom on a 1440px display yields a 720px CSS viewport. 720 < 900. The two
statements are directly incompatible, and the assumption tag makes it worse by
appearing to have considered it. (WCAG 1.4.10 Reflow, which is the AA criterion that
actually bites here, asks for 320 CSS px.) **Fix:** either commit to a real reflow
spec down to 720px (single-column plots, comparison becomes stacked sections) and
delete the 900px cliff, or delete the 200% claim and state the supported floor
honestly. Do not ship both.

### D8. "Every state change is an explicit click" vs. validation on blur

EXPERIENCE.md § Interaction Primitives: *"**Click to act.** Every state change is an
explicit click. **Nothing fires on hover, focus, blur, or scroll.**"*

§ Validation and enablement: *"Validation is **on blur**, not on keystroke."*

Also: field 1 (target column) selection triggers a detection round-trip and renders
six new fields — arguably a click, but it is the single most expensive non-button
action in the product and the ban's spirit is against exactly that. **Fix:** narrow
the ban to what you mean — *"no round-trip fires on hover, focus, or scroll; the only
non-button round-trip is target-column selection, which triggers detection."*

### D9. Missing state: detection in flight

Selecting a target column triggers auto-detection of prediction type, feature types,
missing-value rate, and class balance — a full-column scan of a file that may be
50MB. EXPERIENCE.md specifies the *result* (six fields render, `aria-live` announces
"6 properties detected") and the *failure* ("Detection failed entirely") but **no
in-flight state**. On a large file there is a multi-second window where the user has
picked a target and nothing has happened.

**Fix:** add a state: target `Select` shows an inline progress indicator, the fields
region shows skeletons at final count, `Get Recommendation` stays disabled, and an
`aria-live` polite announcement on completion (already specified).

### D10. Missing state: page refresh / tab close destroys everything

"Nothing is destructive" is governing posture #2. `F5` during a 15-minute training run
destroys the dataset (in-memory only, FR-7.2), all form answers, all results. There is
no session persistence (no auth, no saved sessions), no `beforeunload` guard — and
"confirmation dialogs on non-destructive actions" are banned, which doesn't help
because *this one is destructive*.

Flow 4 is a live projector demo. This is the most likely real-world failure of the
whole product. **Fix:** either (a) persist form answers to `sessionStorage` (not the
dataset — FR-7.2 forbids that) so a refresh costs the file and the run but not the
eleven answers, plus a `beforeunload` guard while a run is in flight; or (b) state
explicitly that refresh is a full reset and add it to the flows.

### D11. Server-side session state is asserted but never specified

EXPERIENCE.md's `Run comparison` contract: *"already-trained methods are reused from
**the session's in-memory result cache** and do not re-train."* The comparison-running
state: *"the recommended reference column is already populated from the earlier run."*

Both require the server to hold the parsed dataset and prior fit results across
independent round-trips, in a product with **no authentication and no sessions**
(NFR-4, Foundation). Where does the 50MB dataframe live between `Get Recommendation`
and `Run comparison`? For how long? What happens if it's evicted? Nothing says. The
alternative — re-uploading the CSV on every action — contradicts the reuse rule.

This is architecture, not UX, but the UX spine **asserts a behavior that constrains
the architecture** and should say so. **Fix:** add one line flagging it as an
architecture dependency: *"comparison reuse requires server-side per-session dataset
and result retention with a stated TTL; if the architecture chooses stateless, `Run
comparison` re-trains and the estimate line must reflect it."*

### D12. Band mapping is engine semantics being decided by the UI

*Remove the dataset* maps detections to Shape B bands ("8,412 rows → `500–10k`"). The
same happens implicitly for missing-value rate (`3.2%` → `none`/`some`/`a lot`) and
feature types. **The thresholds are never specified** — and they are engine inputs
(FR-2.1), so they change the recommendation.

Worse for the research: this means advice-only mode and dataset mode feed the engine
**different-fidelity representations of the same problem**, and FR-6.4's evaluation
compares the recommender against baselines on benchmark datasets (full fidelity) while
real users may be in banded mode. That's a validity gap worth naming.

**Fix:** move the band definitions into the PRD/engine spec, cite them here by
reference, and state in the thesis that advice-only inputs are coarsened.

### D13. FR-5.5 is research data with essentially no spec

*"Did the results match your expectations?"* is one of only two user-satisfaction
metrics in v1 (FR-2.4 is deferred), and it is the **least specified element in either
document**: it appears once, in Flow 4 step 7, as a line the professor ignores. No
component pattern, no placement token, no submit behavior, no confirmation, no failure
state, no free-text length limit, no privacy treatment (see M7).

EXPERIENCE.md's Coverage Check flags this honestly ("the journeys don't dwell on it")
— but honesty about a gap in a research-critical surface is not the same as closing it.

**Fix:** give it a Component Patterns row and a State Patterns row at the same fidelity
as the `Report an error` dialog, which it structurally resembles.

### D14. The "playground" claim is not delivered, and the cheapest fix is missing

The addendum's rationale for rejecting the wizard was that a dashboard *"feels more
like a playground than a tutorial."* EXPERIENCE.md promotes this to a brand claim:
*"a playground with a lab coat on — the page rewards poking."*

Inventory what a user can actually poke without an async round-trip: chart tooltips,
legend click-to-isolate, `View as table`, two accordions. That's it. Every other
interaction is: fill 11 fields → click a button → wait up to 25 minutes. The document
is candid about this ("nothing expensive fires without a click") and then claims
playfulness anyway. As specified, this is a **form-and-report tool that says it's a
playground**.

Two things would actually move it, and neither is in the spec or the PRD:

1. **A sample dataset.** There is no "try it with an example" affordance anywhere. A
   curious visitor with no CSV must hand-fill Shape B — the least playful path in the
   product — and Flow 2 frames the fast, cheap, sub-5-second advice-only mode as the
   *degraded* mode. One `Load an example dataset` button next to the dropzone
   (2–3 pre-parsed classics) converts the entire first-run experience and costs almost
   nothing. It also fixes the demo-reliability problem in D10 for Flow 4.
2. **Make advice-only the front door, not the fallback.** It's <5s (NFR-1), it
   exercises the rule layer that carries the pedagogy, and it's the only loop fast
   enough to reward poking. The spec currently treats it as what you get when you
   *don't* have data.

**Fix:** either add the sample dataset and re-frame advice-only, or drop the playground
language and describe the product as what it is — a deliberate, explicit,
non-reactive analysis tool. The second is a perfectly good thing to be; claiming the
first and shipping the second is what invites the criticism.

---

## MINOR

- **`N of 5` means two different things.** Early halt shows `3 of 5 methods finished`
  (deliberate, good) and partial results shows `4 of 5 methods finished.` (a method
  timed out, bad). Same shape, opposite meaning, and in Flow 1 step 8 Marta sees
  `3 of 5` and "then it stops" with no signal until she reads a caption below. Use
  different constructions: `Trained 3 methods (stopped early)` vs `4 of 5 finished —
  1 timed out`.
- **Stale disables the method chips**, so a user with perfectly good prior results
  cannot start a comparison against them — which cuts against "old results stay
  usable, they answer the old question."
- **Disabled `Get Recommendation` + `Tooltip`** has the same MUI problem the spec
  correctly identified for chips: a truly `disabled` button doesn't fire tooltip
  events. The spec doesn't note it here.
- **`series-other` `#9e9e9e` is byte-identical to `text-disabled` `#9e9e9e`.** An
  "Other" fold in a chart will read as disabled. Shift one.
- **The recommendation panel's contents list (EXPERIENCE.md line 66) omits the "Where
  does this come from?" link**, which the IA table says lives there and Flow 2 step 7
  depends on.
- **`aria-live` chatter.** Polite announcements for detection complete, each `N of 5`
  tick, results ready, early halt, comparison complete, and stale means a screen-reader
  user hears 8–10 interruptions per run. Specify throttling or collapse the progress
  ticks into start/end only.
- **Class balance options are binary-shaped for multiclass.** "Roughly equal / one
  class dominates" (FR-1.3, carried into Shape B) doesn't describe a 12-class
  long-tail. Inherited from the PRD, but the UX is where it becomes visible.
- **`Escape` closes "the topmost Dialog, Menu, or Tooltip"** — hover tooltips aren't
  focus-scoped, so "topmost" is ill-defined for them.
- **Chart count is understated.** "~20 method-specific plots, 4 EDA plots, and a
  benchmark heatmap" omits FR-4.4's four-item library, which DESIGN.md's plot-family
  table also never assigns slot rules to. Actual distinct chart implementations
  ≈ 29.
- **"Feature distributions by class"** (FR-4.4) is an inherently multi-series overlay.
  For any multiclass problem it exceeds the 3-slot scatter cap and the 4-slot line cap,
  and no rule in either spine resolves it.

---

## What I'd fix first, if only three things

1. **B2** — specify what comparison-mode alignment actually is. It's the core feature
   and it currently can't be built.
2. **B1 + M7** — the two findings that are about the *thesis*, not the app. Both are
   cheap to fix on paper and expensive to fix at the defense.
3. **M6** — add Build Tiers with explicit "if cut, remove this claim" lines. This is
   the single change that most improves the odds that what ships and what the thesis
   says about it are the same artifact.
