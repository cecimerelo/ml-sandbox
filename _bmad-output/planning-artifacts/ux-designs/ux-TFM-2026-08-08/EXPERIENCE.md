1---
status: draft
updated: 2026-08-08
project: TFM
name: TFM Recommender
ui_system: MUI
design_spine: ./DESIGN.md
description: Information architecture and behavior for an explainable supervised-learning method recommender. Single-page dashboard plus a benchmark transparency page. Button-triggered, async, non-destructive. Every visual value referenced here lives in DESIGN.md and is cited by token name.
sources:
  - ../../prds/prd-TFM-2026-07-26/prd.md
  - ../../prds/prd-TFM-2026-07-26/addendum.md
  - ./.memlog.md
  - ./DESIGN.md
---

# TFM — Experience Spine

## Foundation

Desktop-first responsive web. No mobile in v1 (NFR-3) — meaning no mobile *design target*, not a broken page: the layout reflows to a single column below 800px and stays operable. See *Responsive & Platform*. Supported browsers per NFR-3: current Chrome, Firefox, Safari, Edge. No authentication, no accounts, no saved sessions — a session is one browser tab, and closing it ends it.

**The UI system is MUI (Material UI), and both spines inherit from it.** `DESIGN.md` inherits MUI's default light theme and spends its budget on the chart layer; **this file inherits MUI's default component *behavior* and specifies only the behavioral delta** — the triggers, transitions, persistence rules, and states that MUI has no opinion about. Where MUI already defines a behavior (Accordion expand/collapse, Select keyboard traversal, Dialog focus trap, Snackbar auto-dismiss), that behavior is the spec and this file stays silent. Where this product needs something MUI does not ship — disabled-with-reason, stale-but-readable, tiered async timeout, early-halt, advice-only mode — this file owns it.

`DESIGN.md` is the visual reference. **No hex code, px value, opacity, or type size appears in this file.** Tokens are cited by name in `{path.to.token}` form; if a behavior needs a look, it names the token and stops. The one exception is **viewport breakpoint values**, which are layout facts about the browser rather than design decisions, and are written as numbers in *Responsive & Platform*.

Two surfaces only. The product is a **playground with a lab coat on** — the page rewards poking, but nothing expensive fires without a click.

**Governing behavioral posture, in priority order:**

1. **Nothing expensive is reactive.** All ML runs on the backend (addendum: client-side ML rejected). Every result is an async round-trip, and every round-trip is user-initiated.
2. **Nothing is destructive.** Changing an input never deletes an answer. Re-running never clears the previous view before the new one is ready. Uploading a dataset never discards form answers that are still valid.
3. **Nothing is hidden to protect the user.** Incompatible methods are disabled with a reason, not removed. Timed-out methods say so. Early-halt says so. A recommendation the engine is unsure about still shows its score.
4. **Nothing the UI does may manufacture the thesis's own result.** Where an interaction is also a measurement, the measurement rule is written down beside the interaction. See *Measurement Behavior*.

---

## Information Architecture

Two surfaces. No nesting deeper than one modal level.

### Surfaces (2)

| Surface | Reached from | Returns to | Purpose |
|---|---|---|---|
| **Dashboard** | App root `/` — the landing surface; the top bar's product title from anywhere | — | The whole product loop: characterize → recommend → explain → explore → compare |
| **Benchmark** | Top bar `Benchmark` link, and the recommendation panel's `Where does this come from?` link | The same top bar — the product title is the home link | Transparency: the dataset × method evidence behind the recommender, dataset provenance, and error reporting |

### Overlays and in-place toggles (5)

| Element | Reached from | Kind |
|---|---|---|
| **Privacy notice** | Persistent footer link on both surfaces; also inline under the upload control | One-level `Dialog` |
| **Report an error dialog** | `Report an error` button on any benchmark row | One-level `Dialog` over Benchmark |
| **Add visualization picker** | `Add visualization` control above the plot grid | One-level MUI `Menu` over Dashboard |
| **View as table** | `View as table` button on a plot panel | In-place toggle inside the panel — not a surface change |
| **Show all methods** | Expander below the promoted-3 chip row | In-place MUI `Accordion` |

### Top bar (block 0, both surfaces)

A real element, present on Dashboard and Benchmark alike, above every block on both surfaces. MUI `AppBar`, `elevation={0}`, with a bottom divider hairline (visual spec in `DESIGN.md § Components → App bar`). It is **not sticky** — it scrolls away with the page. The only sticky element in the product is the collapsed form summary bar, and two competing sticky bars on a long scrolling page is one too many.

> **Settled by the author (2026-08-08).** The top bar is **not sticky**, and `DESIGN.md` agrees (`{components.app-bar}` is `position: static`). The reason is that the sticky form summary bar is load-bearing — it is the one-click route back to the inputs from the bottom of a very long page — and a second permanently-parked bar would compete with it for the same edge on the same scroll.

- **Left:** the product title, rendered as a link to `/`. This is the return path from Benchmark. On the Dashboard it is a same-page link and scrolls to top; it never re-runs anything and never clears state.
- **Right:** a single `Benchmark` text link. On the Benchmark surface it renders as the current page (`aria-current="page"`) and is not a navigation action.
- **Focus order:** the top bar holds the first two tab stops on every surface — title, then `Benchmark`. Both are ordinary links: `Enter` activates, `Tab` moves on. There is no menu, no drawer, no dropdown, and no keyboard shortcut.
- **Skip link:** a visually-hidden `Skip to main content` link precedes the title and is the very first tab stop, so a keyboard user does not re-traverse the bar on every page.

Navigating between surfaces is a full page change. Dashboard state (form answers, results) is held in the tab's memory and survives the round trip; nothing is re-fetched and nothing is re-run on return.

### Dashboard block order (top to bottom, single scrolling column)

Blocks are separated by `{spacing.section-gap}`. Order is fixed — the page never reorders itself.

| # | Block | Present when | Collapsible |
|---|---|---|---|
| 0 | **Top bar** | Always, both surfaces | No |
| 1 | **Upload + Problem characterization form** | Always | Collapses to `{components.form-summary-bar}` after the first `Get Recommendation` |
| 2 | **Recommendation panel** | After first successful `Get Recommendation` | No |
| 3 | **Exploratory analysis (EDA)** | Only when a dataset is uploaded (FR-3.1) | Yes — MUI `Accordion`, collapsed by default (FR-3.2) |
| 4 | **Model results** | Only when a dataset is uploaded, after training resolves | Per method sub-block — see below |
| 5 | **Compare methods** | Only when a dataset is uploaded, after model results exist | No |
| 6 | **Comparison feedback prompt (FR-5.5)** | Only after a comparison run resolves | No |
| 7 | **Privacy notice + footer** | Always | No |

Blocks 3, 4, 5, and 6 are **absent entirely** in advice-only mode (no dataset) — not empty, not disabled, not present-and-greyed. In their place, block 2 ends with a single **upload invitation** panel. See *State Patterns → Advice-only*.

### Block 2 — recommendation panel contents

In order: primary method + `{components.fit-score-meter}` · bias-variance position · interpretability note · key decision factors · the 3 ranked alternatives · **method-selection flowchart** · **method characteristics table** · a `Where does this come from?` text link to the Benchmark surface. All of it renders from the engine's rule layer and is available with or without a dataset. Nothing in block 2 requires training.

### Block 4 — model results contents (resolves rubric B4)

Block 4 renders **every method that was actually trained** — which under FR-8.4 is up to 5, or fewer after an early halt or a timeout. Not the recommended method alone, and not the primary-plus-three-alternatives set.

- One **titled sub-block per trained method**, in this order: the recommended method first, then the remaining trained methods by fit score descending.
- The recommended method's sub-block is **expanded**; every other sub-block is a MUI `Accordion`, **collapsed by default**, its summary row carrying the method name, its CV score, and its state (`finished` / `timed out`). This keeps the initial panel count at that one method's FR-4.2 fixed set — 2–3 panels — rather than ~13, and makes the page length predictable regardless of how many methods trained.
- Inside a sub-block, that method's FR-4.2 fixed plot set renders in the plot grid at the density given in *Responsive & Platform*. Plus any panels the user added via `Add visualization`, appended after the fixed set.
- Expansion state of these sub-blocks persists for the session and is not reset by a re-run.
- **Relationship to block 5.** Block 5 does not duplicate block 4's job. Block 4 is *one method at a time, in depth*. Block 5 is *four methods side by side, on comparable numbers* — it re-renders the selected subset's plots in column-per-method form beneath a shared metrics row. A method can therefore appear in both, and that is intended: block 4 is the reading surface, block 5 is the comparing surface.

### Block 5 — comparison layout (resolves adversarial B2)

Row alignment across method columns is **impossible** and is not attempted anywhere in this product: FR-4.2 gives every method a different fixed plot set, so the intersection of plot types across an arbitrary 4-method selection is frequently empty. Any claim of "the same plot type sits at the same vertical position across columns" is deleted from this spine. The structure is instead two parts:

1. **Shared metrics row** — at the top of the block, genuinely aligned across all method columns, holding **only comparable quantities**: CV score (mean ± SD), accuracy or RMSE (whichever the prediction type calls for), training time, and delta % versus the recommended reference column. Every method has all four, so this row is truly a row. Numbers use tabular figures so columns do not jitter. The recommended method is the leftmost column and shows an em dash rather than `0.0%` in the delta cell (FR-5.2, FR-5.4).
2. **Per-method plot columns** — below the metrics row, each method's own FR-4.2 fixed plot set flows freely down its own column at whatever height it needs. **No cross-column row alignment is attempted or implied.** Column widths are equal; column heights differ, and a column simply ends where its plots end. Each plot carries its own title, so a reader never has to infer what a panel is from its vertical position.

The FR-5.4 ranking list renders below both parts, as a separate list — column order is **selection order** and is never re-sorted by the ranking. `[ASSUMPTION — re-sorting columns after a run would move plots under the user's eye and break the entity↔color binding.]`

**Anchoring.** Each block carries an `id`, and the collapsed form summary bar is sticky, so a user scrolled to the comparison block can always get back to their inputs in one click without scrolling.

### Requirements with no UI surface, stated visibly

- **FR-6.4 (Random-selection and AMLBID baselines) is out of UI scope.** These are thesis-report deliverables — the recommender's accuracy against a lower-bound and an upper-bound baseline is reported in the written evaluation, not rendered in the product. The Benchmark surface says so on the page, in one `{typography.caption}` line beneath the heatmap: `Baseline comparisons — random selection and AMLBID — are reported in the thesis, not shown here.` Stating it in the UI is cheaper than building it and is itself an act of transparency.
- **FR-2.4's behavioral satisfaction measurement has no rendered surface, but it is not free.** It requires the recording rules in *Measurement Behavior*; the feedback *modal* is what FR-2.4 defers to v2, not the measurement.

---

## Measurement Behavior

This product is also an instrument. Three of the thesis's metrics are read out of user interactions, so the interactions have to be defined in terms of what they record. **The UI must never manufacture the result the thesis is testing.**

### The problem this fixes

FR-8.4 auto-trains up to 5 methods ordered by fit score. The recommended method is rank 1 by construction, so it is *always* trained. Any metric of the form "did the user run the recommended method" reads 100% every session and measures nothing. This was previously recorded in the Coverage Check as "Not a gap." **That was wrong.** It is the gap, and it is corrected here.

### System-initiated versus user-initiated runs

The UI distinguishes exactly two origins for a training run, and the origin travels with every method the run trains.

| Origin | What the user did | Which methods it trains | Counts as a deliberate selection |
|---|---|---|---|
| **System-initiated** | Clicked `Get Recommendation` (or `Re-run` from stale) | Whatever FR-8.4's auto-train rule picks — up to the top 5 by fit score, subject to early halt | **Never.** Not for any method in the batch, including the recommended one. |
| **User-initiated** | Toggled one or more method chips on, then clicked `Run comparison` | Only the newly selected methods | **Yes**, but only for the chips the user actually toggled on in that run |
| **Retry** | Clicked `Try again` on a timed-out method's notice | That one method | **No.** A retry inherits the origin of the run that timed out. |

Consequences the UI must honor:

- The recommended method's chip is always present and **not deselectable** (FR-5.2). Its presence in a comparison run is therefore *not* evidence of choice, and is never recorded as one.
- Because the recommended chip cannot be toggled, "the user explicitly selected the recommended method" needs an affordance that actually exists. It is the second question in the FR-5.5 feedback prompt — see below.
- Every deliberate selection is recorded with **where the chip was picked from**: the promoted-3 row or the `Show all methods` expander. The selector is a funnel — 3 methods are one click and the rest are behind an accordion — so the funnel must be a logged covariate rather than an invisible confound.

### What counts as acceptance

**Acceptance is measured on deliberate user choice only.** Two arms, recorded separately and never merged into one number:

- **Arm A (strong).** In the FR-5.5 prompt's `Which method would you use?` control, the user explicitly picks the recommended method. The control is **never pre-filled** and has no default — pre-selecting the recommendation would fabricate the metric a second time.
- **Arm B (weak).** The session ends with no deliberate selection that names a different method — i.e. the user never picked an alternative in the FR-5.5 control. Absence of override is weaker evidence than an explicit pick and must be reported as its own figure in the thesis, never folded into Arm A.

The **diversity counter-metric** obeys the same rule: it is computed over deliberate selections only. Methods that were auto-trained and never chosen do not enter the diversity count, in either direction.

### What this obliges the backend to store

Beyond FR-7.3's existing record: the origin flag per trained method, the selector path per deliberate selection, the promoted-3 set that was offered, and the FR-5.5 answers. This is a change to the PRD's Success Metrics section and to FR-7.3, and is recorded as such in `.memlog.md`.

---

## Voice and Tone

Microcopy only. Brand voice and aesthetic posture live in `DESIGN.md § Brand & Style`.

Three registers, and the product must not blur them:

- **Question labels** — short, second person, no jargon in the label itself. Jargon may appear in the explanation *below* the label, where it is immediately defined.
- **Inline educational explanation** (`{typography.body-educational}`) — plain language, concepts only, **citation-free**. Never names a textbook, paper, author, or year, even when the concept is lifted directly from one. Two to three sentences maximum; the explanation is a doorway, not a lecture.
- **System state** — flat, factual, non-apologetic. The system reports what happened and what the user can do next. No "oops", no "sorry", no exclamation marks, no emoji.

| Do | Don't |
|---|---|
| "Which column are you trying to predict?" | "Select target variable" |
| "Your inputs changed — re-run to update." | "⚠️ Results may be out of date!" |
| "Random Forest can't be used here — your target is a continuous number, and this method predicts categories." | "Incompatible method." |
| "A more complicated method can bend to follow patterns a straight line would miss. That pays off when the real pattern is genuinely complicated *and* you have enough rows to pin it down; with few rows it starts following the noise instead, and does worse on data it hasn't seen." | "Flexible methods bend to fit your data. That helps when the pattern is complex, and hurts when there isn't much data to learn from." |
| "We stopped after 3 methods — the top three scored within one standard deviation of each other, so we didn't train the rest. You can still add them below." | "Early stopping triggered (convergence criterion met)." |
| "Boosting ran out of time on this dataset. The other methods finished." | "Training failed." |
| "This file isn't a CSV we can read." | "Invalid file format: parse error at line 1" |
| "0.87 fit score" | "87% match!" / "Great choice!" |
| "We noticed two columns that often go together. Do they interact?" | "AI detected potential feature interactions" |
| Name the method in full on first use in a block ("Logistic Regression") | Insider shorthand ("LogReg", "RF", "GBM") |

Two of those rows were previously wrong and are corrected here:

- The old flexibility line used **"flexible" as an undefined term of art** and stated the tradeoff approximately-wrongly — complexity hurts when rows are few *relative to how complicated the true pattern is*, not absolutely. The replacement above names no term of art and gets the relation right.
- The old early-halt line claimed *"training more wouldn't have told you anything new."* That does not follow: the top 3 being within 1 SD says nothing about methods 4 and 5, and FR-8.4 orders candidates by the very heuristic FR-6.4 exists to test. The interface must not assert a conclusion the thesis is testing. The replacement describes what happened and what the user can still do.

**Never claim certainty the engine doesn't have.** The fit score is presented as a score, never as a verdict. Copy says "fits your problem well", never "is the best method". This follows the PRD's counter-metrics (recommendation diversity; the most complex method must not be systematically over-recommended), which only make sense if the tool reads as advisory rather than authoritative.

**Never say "we recommend X because ISLR says so."** The theory is real; the citation is banned (FR-2.3). Explanation copy earns its authority from the reasoning being legible, not from a source.

**Never name a user's column in stored or transmitted copy.** Suggestion microcopy may show the user their own column names on screen (they typed them, they are looking at their own file); nothing that leaves the browser carries them. See *Column-name opt-in*.

---

## Component Patterns

Behavioral only. Visual specs live in `DESIGN.md § Components`.

| Component | Behavioral contract |
|---|---|
| **Top bar** | See *Information Architecture → Top bar*. Two links, not sticky, present on both surfaces, first tab stops after the skip link. The title is the home link and the return path from Benchmark. |
| **Upload dropzone** | Click or drag-drop. Accepts one CSV. Validation fires **before** any parse (FR-8.1): extension + MIME + size gate first, then a header-row read. On accept, the dropzone collapses to a filename row with a `Remove` text button. On reject, the dropzone stays open, holds an inline `Alert severity="error"`, and **does not consume the file** — the user can drop another immediately. A large file gets an in-flight state: a determinate `LinearProgress` with a `Cancel` text button; cancelling leaves the form exactly as it was. Removing a dataset returns the form to no-dataset shape but **preserves every always-asked answer** (see *The Problem Characterization Form*). |
| **Form field + inline explanation** | Every question is a field plus a persistent `{typography.body-educational}` line beneath it (FR-1.6). The explanation is **always visible — never behind a tooltip, info icon, or disclosure**. It is not focusable and not a tab stop; it is associated to the field via `aria-describedby` so screen readers get it as the field's description. |
| **Auto-detect confirm row** | A detected value renders as an editable control **pre-filled with the detection**, plus a `{typography.caption}` reading `detected from your file`. The user changes it like any other field; there is no separate "confirm" click for high-confidence fields. Low-confidence fields are the exception — see *State Patterns*. |
| **`Get Recommendation` button** | The only trigger for the whole pipeline (FR-1.7). Non-interactive until every visible required field has a value — implemented with `aria-disabled` and a click handler that does nothing, **not** the `disabled` attribute, so it stays focusable and its `Tooltip` reason stays reachable (the same rule the method chips use). On activation: enters loading, is replaced in place by a `CircularProgress` + estimate line, and stays non-interactive until the round-trip resolves or fails. Never fires on `Enter` inside a text field. `[ASSUMPTION — suppressing implicit form submit prevents an accidental expensive round-trip; the PRD is silent.]` |
| **Form summary bar** | After the first successful run, the form block collapses to one line: the answers as a comma-joined summary, plus an `Edit` text button. Uses `{components.form-summary-bar}` and becomes sticky on scroll. `Edit` re-expands the form **in place, above the results, with results still rendered below**. It is not a modal and it does not scroll-jack; it expands and moves focus to the first field. Collapsing again is via a `Done` button on the expanded form, or automatically on the next `Get Recommendation`. |
| **Fit score meter** | Presentational, per `{components.fit-score-meter}`. Renders the engine's 0–1 score. No interaction, no tooltip, no threshold behavior. The numeral is the value; the bar is the glance. |
| **Method-selection flowchart (FR-2.2)** | **Static and non-traversable.** It is a picture of the decision path the engine actually took for *this* user's answers, with the traversed path emphasized and the untaken branches shown but recessive. The user cannot click nodes, cannot expand branches, cannot pan or zoom, and cannot re-run the path with different answers — changing answers and re-running is how you get a different path. It is **not focusable** and is not a tab stop; it carries `role="img"` with an `aria-label` restating the path as a sentence (`Your target is a category, you have fewer than 500 rows, and you said interpretability is critical — so the path ends at Logistic Regression.`). Beneath it, one text button, `View as steps`, is the only tab stop in the panel; it toggles the graphic for an ordered list of the same conditions in the same order — step number, question, the user's answer, the branch not taken. It **never pans, zooms, or scrolls**: below the collapse width given in `{components.decision-flowchart}` the panel renders the vertical step list *as its only form*, and the `View as steps` button is not rendered, because there is nothing left to toggle to. Widening the panel past that width restores the graphic and the button, in the same toggle state the user last chose. |
| **Method characteristics table (FR-2.2)** | The qualitative, theory-only artifact — **no training data, no round-trip, always present, including in advice-only mode**, where it is the *only* evidence artifact the product delivers. Renamed from "static comparison table" so it never collides with FR-5.3's `Comparison results`; the two names never overlap anywhere in this product. Rows: the recommended method first, then the 3 ranked alternatives, in ranking order — the row order never changes and the table is not sortable. Columns: accuracy potential · interpretability · training speed · handles non-linearity · handles missing values. **The word is the cell's primary carrier and the only thing a screen reader is given**, in the three-step vocabulary `{components.method-characteristics-table}` fixes per axis; the ordinal dot count beside it is a second, redundant carrier of the same step, never a substitute for the word. **No cell carries a series color or a status color** — these are ordinal positions on a theory axis, not health states, and encoding them green/amber/red would assert a verdict the rule layer does not make. The recommended row is identified by **its position and by the treatment in `{components.method-characteristics-table}`**; color is never its sole carrier. It is already a `Table`, so it has no `View as table` toggle and needs none. Below `{breakpoints.single-column}` it scrolls horizontally inside its own panel with the method-name column pinned — it never reflows into cards, because a card per method destroys the across-method comparison that is the table's entire job. |
| **Method chip** | The comparison selector's unit, per `{components.method-chip}`. Click toggles selection. Selection is capped at 3 alternatives (4 total with the recommended method, FR-5.1). The recommended method's chip is always present, always selected, and **not deselectable** (FR-5.2 — it is the reference column). A user toggle from unselected → selected is a **deliberate selection** and is recorded as such with its selector path (see *Measurement Behavior*). |
| **Method chip — disabled with reason** | Incompatible methods are **always rendered, never removed**, per `{components.method-chip-disabled}`. In the promoted-3 row the reason is a `Tooltip`; in the expanded `Show all methods` list the reason is always inline. **This file owns the disabled-chip DOM contract exclusively, and it is the only place it is specified:** `aria-disabled="true"` + `tabindex="0"` + `aria-describedby` pointing at the reason text — **never** the `disabled` attribute, and **never** a `<span>` wrapper. `DESIGN.md` withdrew its `<span>`-wrapper prescription (that wrapper is the MUI workaround for the real `disabled` attribute, which this product does not use) and now specifies appearance only. The consequence is the point: the chip stays focusable, so keyboard and screen-reader users reach the reason. `Enter`/`Space` on a disabled chip does nothing but re-announce the reason. The same three-attribute contract governs every other non-interactive control in this product whose reason the user needs — the `Get Recommendation` button and disabled `Add visualization` menu items. |
| **`Show all methods` expander** | An MUI `Accordion`, collapsed by default, below the promoted-3 chip row. Reveals the full in-scope method list **grouped by area** (Linear Regression / Classification / Regularization / Non-linear / Tree-based / SVM / Deep Learning — the PRD's own grouping). Group order is fixed; within a group, methods sort by fit score descending. `[ASSUMPTION — the PRD gives no sort order inside the full list; fit-score-descending keeps the expander consistent with the promoted row.]` Expansion state persists for the session and is not reset by a re-run. Selections made here carry the `show-all` selector path. |
| **`Run comparison` button** | Sits below the selector. Non-interactive when zero alternatives are selected. Triggers training for the *newly selected* methods only — already-trained methods are reused from the session's result cache and do not re-train, **but only while the input snapshot is unchanged**; see *Re-run and cache invalidation*. This is a **user-initiated** run. |
| **`Stop training` button** | Present only while a training run is in flight. Halts the run after the method currently training. Every method that already finished stays on screen; the rest are marked `not trained — you stopped the run` and remain selectable in the comparison selector. Stopping is not a failure state and does not carry an `Alert`. |
| **Plot panel** | Renders one chart, per `{components.plot-panel}`. `View as table` toggles the panel in place between chart and `Table`; the toggle is per-panel, is **not** remembered across re-runs, and never changes panel height. The mechanism: the table renders **inside the panel's existing plot box** with internal vertical scroll and a sticky header row, so the panel's outer height is identical in both modes and the grid above never reflows. Hover on the panel is a border-color change (per `DESIGN.md § Elevation & Depth`), never a lift. |
| **`Add visualization` control** | One control above the plot grid, not per-panel. Opens a `Menu` listing the closed library (FR-4.4): learning curve · calibration curve *(classification only)* · feature distributions by class *(classification only)* · pairwise feature scatter coloured by target. Items invalid for the current prediction type are **disabled with reason**, matching the method-chip rule — as is `feature distributions by class` above the facet cap, whose reason names the class count (`Your target has 9 classes — this plot stops being readable above 6.`). Already-added items render checked and disabled — the same plot cannot be added twice. Selecting one appends a plot panel to the end of the current method's sub-block and triggers its own async fetch — additions are **additive only**; nothing is removed and the fixed set (FR-4.2) can never be turned off. |
| **2-D projection feature swap** | Two `Select`s in the controls row above the plot grid, pre-filled with the auto-selected 2 most important features (FR-4.3). Changing either re-fetches **only the boundary plots**, not the whole result set. The pair is validated distinct — selecting a feature already in the other slot swaps them rather than erroring. The swap is **not** an engine input and never stales results. `[ASSUMPTION — swap-on-collision is the least surprising resolution; the PRD is silent.]` |
| **Delta badge** | Presentational, per `{components.delta-badge-up}` / `{components.delta-badge-down}` / `{components.delta-badge-tied}`. The tied case renders the word, not a number (FR-5.4). |
| **Comparison results (FR-5.3)** | The empirical artifact: shared metrics row + per-method plot columns + ranking list, exactly as specified in *IA → Block 5*. Dataset-only. Never called "the comparison table"; that name is retired to avoid collision with the *Method characteristics table*. |
| **Comparison feedback prompt (FR-5.5)** | Renders as block 6 the moment a comparison run resolves; never before. Two questions. **(1)** `Did the results match your expectations?` — a `RadioGroup`, `yes` / `partly` / `no`, **optional**. **(2)** `Which method would you use?` — a `Select` listing exactly the methods in this comparison, **no default, never pre-filled with the recommendation**, also optional. Below both, an optional free-text `TextField multiline` with a stated character cap shown as a live counter, carrying the microcopy `Please don't paste column names or anything that identifies your data.` One `Send` button, non-interactive until at least one of the three has a value. On submit: the block is replaced in place by a `{typography.caption}` line, `Thanks — that's recorded.`, and does not re-render for the rest of the session even after a second `Run comparison`. On submit failure: the block stays exactly as the user left it, keeps every typed character, and shows an inline `Alert severity="error"` with a `Try again` action — **input is never discarded on failure**. Nothing else on the page changes, in either case. |
| **Benchmark heatmap cell** | Visual spec in `DESIGN.md § Components → Benchmark heatmap`. Hover or focus reveals **data only**: dataset name, dataset source (OpenML-CC18 or UCI, per FR-6.3), method, score, and the agree/disagree marker. It carries **no action** — see the next row. Cells are a roving-tabindex 2-D grid (see *Interaction Primitives*). |
| **`Report an error` button** | A **persistent per-row button in a row-header column**, not an affordance inside a hover tooltip. Tooltip content is not pointer-reachable and is not in the tab order, so an action placed there is unreachable for half the product's users and contradicts *Hover reveals information, never actions*. `Enter` on the roving grid cursor opens the focused cell's row dialog. Opens a one-level `Dialog`. |
| **Privacy notice** | Always-present footer link plus a `{typography.caption}` line directly under the upload control carrying the short form. Opens a `Dialog`, not a new surface. Never a dismissible banner, never a consent gate — the product does not block on it. The dialog states, in the same three-register voice: the dataset is never written to disk; which decision drivers are stored; and that **no column name and no cell value ever leaves the browser as part of the stored record**. |

---

## The Problem Characterization Form (FR-1)

The form is the product's front door and its only expensive trigger. It is a **full-width top block**, never a sidebar (locked).

### Shape: adaptive on dataset presence

The form has exactly two shapes. Uploading or removing a dataset switches shape.

**Shape A — dataset uploaded (FR-1.2).** Field order:

1. **Target column** — `Select` listing every column name. **Nothing below this field renders until a target is chosen**, because every detection depends on it. This is the form's only sequential dependency.
2. **Prediction type** — auto-detected from the target's value types (regression / binary classification / multiclass). Confirmable.
3. **Row count** — auto-detected. **Read-only display**, not a control — it is a fact about the file, not an opinion. Shown as an exact number with its band in `{typography.caption}` (`8,412 rows · medium`).
4. **Feature count** — auto-detected. Read-only, same treatment.
5. **Feature types** — auto-detected (numeric / categorical / mixed). Confirmable.
6. **Missing value rate** — auto-detected, shown as a percentage plus its band. Confirmable.
7. **Class balance** — auto-detected. **Rendered only when prediction type resolves to binary or multiclass classification.** Disappears immediately if prediction type is changed to regression; its value is retained in state and restored if the user changes back. `[ASSUMPTION — retain-and-restore rather than clear; consistent with the non-destructive posture.]` **The option set depends on the prediction type**, because the PRD's two options are binary-shaped and do not describe a 12-class long tail: at **binary** the control offers `roughly equal` / `one class dominates`; at **multiclass** it offers `roughly equal` / `one class dominates` / `several classes are rare`. The third option maps to the same engine band as `one class dominates` until the engine spec says otherwise — it exists so a user with a long tail is not forced into a description that is false. `[ASSUMPTION — FR-1.3 defines two options and does not distinguish binary from multiclass; flagged for the author because a third band, if the engine wants one, is an engine change and not a UI one.]`
8. **Column-name opt-in toggle** — see below.

`[ASSUMPTION — row count and feature count are read-only while the other four detections are confirmable. FR-1.2 lists all six under "displays for user confirmation", but a user cannot meaningfully disagree with a row count. If the author wants all six editable, make 3 and 4 banded Selects matching Shape B.]`

**Shape B — no dataset (FR-1.3).** All answers are manual and banded. Field order: prediction type · rows (`< 500` / `500–10k` / `> 10k`) · features (`< 10` / `10–50` / `> 50`) · feature types (numeric / categorical / mixed) · missing values (`none` / `some` / `a lot`) · class balance *(classification only; same conditional render-and-retain rule and the same prediction-type-dependent option set as Shape A field 7)*.

**Always asked, in both shapes, appended after the shape-specific fields (FR-1.4):**

9. **Explainability importance** — `not important` / `somewhat` / `critical`.
10. **Non-linearity suspicion** — `no` / `unsure` / `yes`.
11. **Feature interactions** — a three-option `RadioGroup` matching its two siblings: `no` / `unsure` / `yes`. When the answer is `yes` **and** a dataset is uploaded **and** the column-name toggle is on, a secondary `Autocomplete multiple` appears directly beneath it, pre-populated with the system's suggested column pairs (FR-1.5), from which the user can accept, remove, or add pairs by picking two column names. Without a dataset the `yes` answer stands alone with no follow-up, because there are no column names to name. The engine (FR-2.1) consumes the three-option answer; the named pairs are additional local signal, never required, and **never stored by name** — see *Column-name opt-in*. `[ASSUMPTION — FR-1.4 poses this question but defines no answer type; the three-option shape is chosen so all three always-asked questions share one answer shape and one visual rhythm.]`

**Band thresholds are engine semantics, not UI choices.** The mapping from an exact detection to a band (`8,412 rows → 500–10k`, `3.2% missing → some`) is used in two places — the Shape B controls and the dataset-removal carry-over — and it changes the recommendation, so it is an engine input. The thresholds live in the PRD/engine spec and are cited here by reference, never redefined. This spine records the consequence: **advice-only mode feeds the engine a coarser representation of the same problem than dataset mode does**, and the thesis must say so when it compares the recommender against FR-6.4's baselines, which run at full fidelity.

### Shape switching: what persists, what resets

| Transition | Persists | Resets |
|---|---|---|
| Upload a dataset into an empty form | Fields 9–11 | Nothing — fields 1–8 did not exist |
| Upload a dataset over a filled Shape B form | Fields 9–11, verbatim | Fields 2–7 are **discarded and replaced by detections**, shown with the `detected from your file` caption. The user's prior manual bands are not shown as a diff. `[ASSUMPTION — the file is ground truth; reconciling two sources would be a confusing surface. The PRD is silent.]` |
| Remove the dataset | Fields 9–11. Fields 2–7 **carry over as manual bands**, mapped from the detected values (8,412 rows → `500–10k`), so the user is not re-answering questions the file already answered | Target column, column-name toggle, interaction pair suggestions |
| Replace one dataset with another | Fields 9–11 | Target column and all detections — re-detected against the new file |
| `Edit` on the collapsed summary bar | Everything | Nothing |

**Removing a dataset never destroys results.** Existing model results and comparison go stale (dimmed + banner) rather than disappearing, and the blocks remain until the next `Get Recommendation`, which then rebuilds the page in advice-only shape. Note that dataset removal is a **one-way stale** — see *State Patterns → Un-stale without re-running*.

### Column-name opt-in (FR-1.5) — and what leaves the browser

A `Switch` labelled **"Use column names to improve suggestions"**, default **ON**, rendered **only in Shape A**.

- **ON** → after target selection resolves, the system proposes interaction pairs. Proposals surface as microcopy on the feature-interactions question and as pre-populated chips in the pair `Autocomplete`.
- **OFF** → no proposals; the pair `Autocomplete` still exists and is still manually usable. Turning the toggle off **clears system-proposed pairs but keeps user-added pairs.** `[ASSUMPTION]`
- Toggling never triggers a round-trip. Suggestion generation is local to the already-parsed header row.
- Toggling **never stales results** — the toggle is not an engine input.

**The privacy resolution (adversarial M7).** Three statements previously could not all be true: the toggle promised column names are used *only* for interaction suggestions; the user's named pairs were described as engine signal; and FR-7.3 permanently stores "feature interactions" as a decision driver. If named pairs entered the stored record, the toggle's promise was false and "anonymized" was doing work it cannot do — column names from a private dataset are frequently identifying of the dataset and sometimes of its domain. For a Spanish master's thesis this is a GDPR question a committee can reasonably ask.

**Resolved by anonymizing, not by weakening the copy.** The stored form of an interaction is the *fact* of one, never the names:

- What is stored per session: the three-option answer (`no` / `unsure` / `yes`), the **count** of confirmed pairs, and for each pair a flag for whether it was system-suggested or user-added. That is enough to analyse whether interaction signal changes recommendations.
- What is **never** stored, never logged, and never transmitted as part of the record: the column names themselves, in any form — not plaintext, not hashed. A hash of `patient_id` is still a stable identifier for `patient_id`; hashing would let the notice keep saying "we store names" in a costume.
- Column names exist only in the browser and in the in-memory request that produces the recommendation, which FR-7.2 already forbids persisting.
- Because that is now literally true, the toggle's explanation can say so without hedging, and the consent-free posture (`never a consent gate`) stays defensible.

The toggle's inline explanation, verbatim:

> **Use column names to improve suggestions**
> We read your column *names* — never the values in them — to guess which pairs of columns might interact. That guess happens in your browser and nothing about your column names is ever saved or sent anywhere. Turn this off and you can still name pairs yourself.

The suggestion microcopy on question 11 may show the user their own column names on screen (`We noticed \`age\` and \`income\`. Do these interact?`) because those names never leave the tab. The FR-5.5 free-text field is the one place a user could type a column name into something that *is* stored, which is why that field carries an explicit ask not to.

**Author decision flagged:** option (a) — anonymize — was taken over option (b) — hash and qualify the notice. If the research later needs the names, that is a PRD-level change with a consent surface attached, not a microcopy edit.

### Validation and enablement

- `Get Recommendation` is non-interactive (`aria-disabled`) until every visible required field has a value. It does **not** turn red, and no field shows an error before the user has interacted with it.
- Validation is **on blur, not on keystroke.** A field the user hasn't left yet is never wrong. Blur validation is a local, non-round-trip state change and is the stated exception to *Click to act* — see *Interaction Primitives*.
- The non-interactive button carries a `Tooltip` naming what's missing (`Choose a target column to continue`), reachable because the button is `aria-disabled` rather than `disabled`.
- Low-confidence detections **do not block** the button — they flag for confirmation (FR-8.2). See *State Patterns*.

### Focus and keyboard

- Tab order is strictly visual order: field → next field. Explanation text is skipped.
- On upload success, focus moves to the **target column** `Select`.
- On target selection, detection begins (see *Detection in flight*); focus **stays** on the target `Select` (no focus steal). When detection completes, an `aria-live="polite"` region announces `6 properties detected from your file. Review them below.`
- On `Get Recommendation`, focus moves to the recommendation panel heading once results resolve, and the panel scrolls into view. On failure, focus moves to the error `Alert`.
- On `Edit`, focus moves to the first field of the re-expanded form.
- `Escape` inside the expanded form does nothing (it is not a modal). Collapsing is explicit.

---

## The Explanation Layer

Education is not a section — it runs through the whole product. It has exactly **four placements**, and nothing outside them is educational.

| Placement | What it is | Rules |
|---|---|---|
| **Under every form question** | `{typography.body-educational}`, always visible (FR-1.6) | 2–3 sentences. Defines the concept *this question* needs, not the concept generally. Never behind a tooltip or icon. |
| **In the recommendation panel** | Bias-variance position, interpretability note, key decision factors | `{typography.body}` prose. Key decision factors name the user's **own answers back to them** ("small dataset + interpretability critical → Logistic Regression preferred over Random Forest"), so the explanation is traceable to inputs, not to authority. |
| **`{typography.chart-subtitle}` on every plot** | The beginner-facing "what am I looking at" line | Default-on for any plot a beginner won't recognise — which per `DESIGN.md` is most of them. It describes **how to read the chart**, not what the result means. |
| **Disabled-with-reason text** | Why a method or visualization can't be used here | The reason is about the *user's problem*, not about the system. "Your target is a continuous number, and this method predicts categories" — not "task type mismatch". |

**Hard constraints on all four:**

- **Citation-free.** No textbook, paper, author, year, or "the literature". The underlying theory is ISLR; the UI must never say so, imply so, or link out to it.
- **No prior knowledge assumed.** Any term of art used in an explanation is defined in that same explanation, or is not used.
- **No explanation asserts a claim stronger than the engine rule that consumes it.** If the rule layer only knows "few rows + interpretability critical → prefer a simpler method", the copy may not say the simpler method *is better*; it says why it was preferred.
- **Explanation copy is static and pre-authored** for form questions, chart subtitles, and disabled reasons; it is engine-generated only for the recommendation panel's decision factors.
- **No progressive disclosure of education.** There is no "learn more", no expandable glossary, no tour, no first-run coach marks. A wizard was rejected upstream; a tutorial layered on top of a dashboard is the same rejected idea wearing a coat.

### The copy is a real, countable deliverable

Counting from this spec: 11 form questions × 1 explanation (plus Shape A/Shape B variants where the question differs) · one `chart-subtitle` per distinct chart form (~29 including FR-4.4's library) · disabled reasons across the in-scope methods × 3 prediction types, which templates down but does not vanish · plus state messages. That is a low-hundreds body of pre-authored, plain-language, citation-free, pedagogically defensible strings, and it is the pedagogical heart of the thesis. It needs three things this spine now names:

1. **Where it lives.** A single string catalogue in the front-end source, keyed by string ID, with one entry per string. Not inline in components. It is reviewable as one artifact because a supervisor has to be able to read it as one artifact.
2. **Who reviews it.** The supervisor signs off the catalogue as content, separately from the code.
3. **How it is grounded.** A **copy → source-section traceability table maintained as a thesis appendix, never in the UI.** The UI stays citation-free per FR-2.3; the appendix proves the pedagogy is grounded. This converts the single most likely defense question — "how do you know these explanations are correct?" — from a risk into an exhibit.

### Copy specimen set

One fully-written specimen per string class, at final length. These are the templates: if a new string cannot be written to this standard, the placement is not shippable.

**Class 1 — form question label + explanation.** Question 10, both shapes:

> **Do you think the pattern in your data is a straight line?**
> Some methods can only draw straight relationships — as one number goes up, the other goes up or down at a steady rate. Others can bend. If you already know the relationship curves, levels off, or flips direction somewhere, say so and we'll prefer a method that can follow it. If you don't know, say so — that's a real answer and we'll treat it as one.

**Class 2 — chart subtitle.** ROC curve panel:

> Each point is one cut-off for calling a case positive. Further toward the top-left means the model catches more real positives for fewer false alarms; the diagonal is what you'd get by guessing.

**Class 3 — disabled reason.** Naive Bayes offered on a regression problem:

> Naive Bayes can't be used here — you're predicting a number, and this method only sorts things into categories.

**Class 4 — state message.** Early halt, at the top of block 4:

> We stopped after 3 methods — the top three scored within one standard deviation of each other, so we didn't train the rest. You can still add them below.

Note what each specimen does and does not do: no term of art is used without being unpacked in the same breath; no source is named; nothing claims a verdict; and the state message describes what happened rather than what it implies.

---

## Chart Behavior Contract

~29 chart forms share one behavioral contract, exactly as they share one visual system in `DESIGN.md § Data Visualization`. A plot panel that breaks any of these is a bug, not a variant — subject to the reductions explicitly permitted in *Scope Tiers*.

**The series cap is a behavioral rule, not a style note** (from `DESIGN.md`'s palette validation):

- **Overlaid lines, grouped/stacked bars** (ROC overlay, CV-error curves, train-vs-test by iteration): up to **4 series** — `{colors.series-1}` through `{colors.series-4}`.
- **Scatter, decision boundaries, pairwise feature scatter, small multiples**: **cap at 3 series.** Any form where two marks can end up side by side.
- **Consequence for the 4-method comparison.** FR-5.1 allows 4 methods. In comparison mode: ROC overlays may render all 4 in one frame; **decision boundaries and pairwise scatter never do — they render one panel per method in the column layout**, single-series each, which the column-per-method structure already provides. There is no 4-series boundary plot anywhere in this product.
- **Consequence for multiclass — three bands, and the third is a refusal.** The facet decision is made by the system from the class count and is **never offered as a user choice**; `DESIGN.md` sets a **hard cap of 6 facets**, and the behavior above it is not "more facets", it is *no plot*.
  - **≤ 3 classes** — one frame, slots 1–3, marker shape per class.
  - **4 to 6 classes** — the plot **facets one-vs-rest**: one small-multiple panel per class, each single-hue, shared axes and shared scale; or the tail folds into `{colors.series-other}`. The panel's `{typography.chart-subtitle}` states what happened: `Shown one class at a time — 5 classes don't separate reliably by colour in one frame.`
  - **More than 6 classes** — the boundary plot is **not rendered at all**. Not faceted, not truncated to the first 6, not collapsed into `{colors.series-other}`: absent. The panel still renders at its normal height and carries a `{typography.body}` line in place of the chart, so the grid never changes shape and the absence is never silent. **What the user is told**, verbatim, per *Scale Guards*: `Boundary plots aren't shown above 6 classes — the picture stops being readable.` No `Alert`, no error styling — nothing is wrong; a plot was declined. There is **no override, no "show anyway", and no user control** anywhere in this product that raises the cap, because 100 facets is not a visualization and offering it would only move the failure downstream. The method's remaining FR-4.2 plots render normally. The panel has **no `View as text` toggle in this case** — there is no projection and therefore no summary of one; the `{typography.body}` line *is* the panel's whole content, and it is already text, already in the accessibility tree, and already reachable without a toggle.
- **Consequence for FR-4.4's "feature distributions by class".** It is an inherently multi-series overlay and exceeds both caps on any multiclass problem. It obeys the identical three bands: one overlaid frame at ≤ 3 classes; **small multiples, one panel per class, single-hue** from 4 to 6; and above 6 it is **not offered at all** — the `Add visualization` menu item is disabled-with-reason rather than added and then refused, so the user learns the limit before spending a click.

**Color follows the entity, not the rank.** The recommended method holds `{colors.series-1}` for the entire session. Alternatives take slots 2, 3, 4 **in the order the user selected them**. When FR-5.4's ranking comes back and reshuffles the order, **nothing repaints.**

**The slot rule, stated so it survives the cap** (fixes the self-defeating no-backfill rule):

- **Already-rendered methods never repaint.** That is the whole point of the rule, and it is the guarantee that survives.
- Deselecting a method **frees its slot**. It does not renumber anything: the two remaining alternatives keep the slots they had.
- A **newly selected** method takes the **lowest free slot**, which after a deselect is the freed one. This is the only way the rule can work at the 3-alternative cap, where there is no slot 5.
- Consequence, stated plainly: a slot's color identity is stable for as long as a method holds it, not for the whole session. A method that occupied slot 2, was deselected, and is later re-selected may come back on a different slot. It comes back with a legend and a direct label, so the chart is still readable; it does not come back with a promise it never had.

**Per-chart behavior:**

- **Every plot ships a hover layer.** Line/area → crosshair + tooltip on shared x. Bar/dot/heatmap cell → per-mark tooltip. Hit targets exceed the marks.
- **Legends are click-to-isolate.** Isolating a series does not repaint the others. Clicking again restores all. Isolation is per-panel and resets on re-run.
- **Loading.** Each plot panel loads independently with a `Skeleton` at its final `{spacing.plot-aspect}`, so the grid does not reflow as results arrive. A method's panels appear **together** when that method resolves — never one plot at a time.
- **Failure.** A plot whose data fails to compute shows an inline message inside its own panel and **does not remove the panel** — the grid holds its shape.
- **No animation on data change.** Plots render at final state. `[ASSUMPTION — consistent with DESIGN.md's "never animate the dim", and the correct default under `prefers-reduced-motion`, which this product honors globally.]`
- **Controls that reconfigure plots live in one row above the grid**, never per-panel: the 2-D feature swap and `Add visualization`. Both go non-interactive when results are stale.
- **The panel floor behaves differently above and below 800px, and the rule is stated in both halves.** It is a consequence of the visual floor in `DESIGN.md`, enforced by the layout, not by the chart.
  - **At and above `{breakpoints.single-column}`:** `{spacing.plot-min-width}` is a **hard panel floor**. A grid that cannot give every panel the floor **drops to fewer columns** — and, failing that, a plot **wraps to its own row rather than shrinking**. No panel is ever squashed below the floor in this range.
  - **Below `{breakpoints.single-column}`:** the floor **yields, inward rather than outward**. The **panel shrinks to the viewport**, and the **plot area inside it holds `{spacing.plot-area-min}` and scrolls horizontally within the panel**. Column-dropping is already exhausted at this point — the page is single-column — so shrink-plus-inner-scroll is the only remaining move, and it is the correct one: it keeps the chart legible instead of keeping the panel wide.
  - **At every width, in both ranges:** a chart whose intrinsic minimum exceeds the plot-area floor — the benchmark heatmap, the correlation heatmap at its cap, a wide tree diagram — scrolls **inside its own panel**. This is not a below-800px special case; it is the same mechanism, and it is why the page **never scrolls horizontally at any width or any zoom**. That guarantee, not the panel floor, is what the 200%-zoom claim in *Accessibility Floor* rests on.

### Text equivalents, per plot family

`View as table` is doing heavy load-bearing work — it is the relief channel for the sub-3:1 series slots *and* the screen-reader fallback — and it is underspecified precisely where it is hardest. Specified per family, so the claim matches what can actually be built:

This table is the behavioral face of `DESIGN.md § Table-view form per family` and **must not diverge from it**: that section decides *what form* each family's equivalent takes; this one decides what the control is called, what the content has to contain to count as equivalent, and what happens when it can't be produced.

| Family | Text equivalent | What it contains |
|---|---|---|
| ROC, calibration, tuning curves, learning curve, train-vs-validation, OOB / error-by-iteration, **shrinkage path, partial dependence** | **Table** | The plotted series as columns, x as rows. Downsampled to a stated row count if longer, with the header saying so. For shrinkage paths the rows are the lambda steps and the columns the coefficients, so the order in which coefficients reach zero is readable off the table rather than described. |
| Coefficient plot, feature importance, variable inclusion proportions | **Table** | Feature, value, rank — **the full list, not the chart's top-K fold.** This is the one place the truncated tail is recoverable, which is why the fold line and this table are specified together. |
| Confusion matrix, correlation heatmap, benchmark heatmap | **Table** | The matrix itself, with real row and column headers and no color fill. For all three this is the *better* representation, not a fallback — and for the benchmark heatmap it is the primary reading mode for anyone using a screen reader. The correlation table is bounded by the chart's own top-K cap, so there is no case where it exceeds what the chart shows. |
| Histogram, boxplot, target distribution, categorical bar | **Table** | Bin or category, count, percentage; the five-number summary for a boxplot. |
| Residual plot, predicted-vs-actual, pairwise scatter, class-conditional distributions | **Table of summary statistics**, never the raw point cloud | A 14,000-row per-point table is not an equivalent, it is the same problem in a different element. Contains: n, mean, SD, min/max, and the fit statistic the plot exists to show (R², RMSE). |
| **Decision boundary** | **Text summary** — no meaningful table exists | It is a 2-D prediction raster; there is nothing tabular to serialize. Contains: the two projected features, the per-class point counts, and the training accuracy on the projection. |
| **Tree diagram** | **Text summary** — no meaningful table exists | The rendered split conditions as an ordered list in traversal order, each with its sample count and predicted value, plus the truncation statement (`Showing the first 3 of 11 levels.`). |
| **Method-selection flowchart** | **Text summary** — the ordered step list | Step number, question, the user's answer, and the branch not taken. This is the same artifact `View as steps` produces and the same one the panel falls back to below its collapse width; it is not a second implementation. |

**Every panel that renders a chart carries one or the other, always.** The single exception is a panel that renders *no* chart — the above-6-class boundary case — whose entire content is already the text that says so. Exactly **three families ship a text summary rather than a table** — decision boundary, tree diagram, and the method-selection flowchart — and for those the button reads `View as text` (or, for the flowchart, `View as steps`) rather than `View as table`. Everywhere else it is a real `Table`. The accessibility claim is stated in exactly those terms and never as a blanket "table" — see *Accessibility Floor*. Direct labelling on the marks is the *primary* relief for slots 3 and 4, because it lives in chart code that is being written anyway; the text equivalent is the second channel, not the only one.

---

## State Patterns

Every state names its trigger, its treatment, its exit, and what survives it.

### Training execution model — decided, because two states depended on it

Early halt (FR-8.4) requires **sequential** training: you cannot decide to stop after 3 methods if all 5 already started. Per-method streaming progress is nicer under parallelism. The spines previously assumed both and reconciled neither.

**Decision: training is sequential, and early halt stays.** Rationale: early halt is a stated PRD requirement with a user-visible disclosure and a real cost saving; per-method streaming works fine under sequential execution — each method's panels land as it finishes, which is exactly the same streaming behavior, just with a longer tail. What sequential execution costs is *wall-clock honesty*, which the estimate model below now pays for openly, plus a `Stop training` control so the tail is the user's choice.

Everything downstream is consistent with this: methods train one at a time in fit-score order; `N of 5` ticks once per method; early halt is evaluated after each method completes from method 3 onward; the estimate is a ceiling derived from *remaining methods × per-method timeout*.

### The loading estimate model (fixes adversarial B3)

The previous estimate presented FR-8.4's **per-method** timeouts as **whole-run** estimates, understating the ceiling by up to 5× — and 25 minutes was displayed as "up to 5 minutes". An estimate wrong by an order of magnitude in the *longer* direction is worse than no estimate, because it is the condition under which a user reloads the page and loses everything.

The estimate line is derived, not written by hand:

- **Ceiling** = `methods still to train × the tier's per-method timeout`. Tiers per FR-8.4: 60s (< 500 rows) / 120s (500–10k) / 300s (> 10k).
- The ceiling is stated as a ceiling, in the same sentence as the fact that results stream. It is **recomputed after each method finishes**, so the number only ever goes down.
- The line also carries live progress: which method is training now, and how many are done.
- The tier's per-method limit is named, so the ceiling is checkable rather than magic.

Rendered form, at the start of a 5-method run on a large dataset:

> Training up to 5 methods, one at a time. Each gets at most 5 minutes, so the longest this can take is 25 minutes — usually much less, and you'll see each method's results as it finishes. **Method 1 of 5 · Random Forest**

And after two finish:

> 3 methods left, at most 15 minutes. **Method 3 of 5 · Boosting**

A `Stop training` button sits beside it throughout.

### Dashboard lifecycle

| State | Trigger | Treatment | Exit / what survives |
|---|---|---|---|
| **Initial / empty** | App load, nothing entered | Top bar, block 1 (upload + form), footer. No placeholder cards, no skeleton results, no "your results will appear here" scaffolding — the page is short on purpose. One `{typography.body}` line above the form frames the product in a sentence. | First `Get Recommendation` |
| **Detection in flight** | A target column is selected | The target `Select` shows an inline indeterminate progress indicator; the fields region below renders `Skeleton`s at the final field count so the block does not jump when they land. `Get Recommendation` stays non-interactive. Focus does not move. On completion, the `aria-live="polite"` announcement fires. A full-column scan of a large file is not instant, and an unexplained multi-second gap after the single most consequential click in the form reads as a broken page. | Detections render, or *Detection failed entirely* |
| **Loading — advice only** | `Get Recommendation`, no dataset | Button → `CircularProgress` in place. **No estimate line** (NFR-1: under 5 seconds). The form is not re-submittable while in flight. | Resolves to Advice-only |
| **Loading — training** | `Get Recommendation` or `Run comparison`, dataset present | Button → `CircularProgress` + the derived estimate line above, plus `Stop training`. Result blocks show `Skeleton` panels at final aspect. Methods train sequentially; each method's panels render the moment that method resolves. The progress line updates once per method, not continuously. | Resolves per-method; see Partial results |
| **Advice-only (no dataset)** | Recommendation resolved with no dataset | Blocks 0 + 1 + 2 + 7 only. Blocks 3–6 are **absent**. Block 2 ends with an **upload invitation** panel: `Upload a CSV to see this method run on your data — exploratory plots, model results, and side-by-side comparison unlock with a dataset.` plus an `Upload a dataset` button that scrolls to and focuses the dropzone. It is a normal panel, not an `Alert`, and is never dismissible. The method characteristics table and the flowchart are fully present here — they are this mode's evidence. | Uploading a dataset + re-running |
| **Full results** | Training resolved, dataset present | All blocks. EDA `Accordion` collapsed; non-recommended method sub-blocks collapsed. | — |
| **Stale** | An **engine-input** answer changes after a successful run — see the snapshot definition below | Blocks 2–6 take `{components.stale-results}`. A sticky banner at the top of the results region: `Your inputs changed — re-run to update.` with a `Re-run` action that fires the same pipeline as `Get Recommendation`. The banner is never dimmed. **Plot-reconfiguring controls go non-interactive** (feature swap, `Add visualization`) — but plots stay hoverable, tooltip-able, and text-equivalent-able, **and the method chips stay live**, so a user can still start a comparison against results that answer the old question. Old results stay readable. **Never animate the dim.** | `Re-run` or `Get Recommendation`. Nothing is destroyed meanwhile. |
| **Un-stale without re-running** | The user reverts every changed engine input to its snapshot value | The dim lifts and the banner disappears. No round-trip — the results were never wrong, only unmatched. | — |
| **Re-running from stale** | `Re-run` | Dimmed results stay on screen beneath `Skeleton`s as each block refreshes. **Results are never cleared before replacements exist.** The result cache is invalidated first — see below. | New full results |
| **Comparison running** | `Run comparison` | Only the comparison block enters loading — the recommendation panel, EDA, and single-method results stay live and interactive. Selector chips go non-interactive for the duration. Each column fills in as its method resolves; the recommended reference column is already populated from the earlier run and never re-renders. | Comparison results + ranking + block 6 |
| **Page refresh or tab close** | `F5`, navigation away, tab close | **This is destructive and the product says so rather than pretending otherwise.** Form answers are mirrored to `sessionStorage` and restored on reload, so a refresh costs the file and the run but not the eleven answers. The dataset is never persisted (FR-7.2) and results are not restored; on reload the page returns to *Initial / empty* with the answers pre-filled and a `{typography.caption}` line above the form: `Your answers were restored. Upload your file again to re-run.` While a training run is in flight, a `beforeunload` guard fires the browser's native prompt — the one case in this product where an interruption warning is warranted, because the action genuinely destroys work. | Re-upload + re-run |

### The input snapshot (what stales, what does not)

Staleness is computed against a **snapshot of the engine inputs only** — FR-2.1's list: prediction type, row count, feature count, feature types, missing value rate, class balance, explainability need, non-linearity suspicion, and the three-option feature-interactions answer. Nothing else is in the snapshot, and it is canonicalized before comparison:

- Numeric detections are compared **as bands**, never as raw values, so the comparison is on the representation the engine actually consumed.
- The interaction-pair set is compared **order-normalized and direction-normalized** — `[(a,b),(c,d)]` equals `[(c,d),(a,b)]`, and `(a,b)` equals `(b,a)` — so an un-stale never fails for a reason the user cannot see.
- The dataset is identified by a **content hash computed at upload**. Two files with the same bytes are the same dataset.

**Explicitly excluded from the snapshot**, and therefore never causing stale: the column-name toggle (not an engine input — flipping a privacy switch must not dim four minutes of plots), the pair-suggestion source, the 2-D feature-swap selections, `Add visualization` additions, accordion and `View as table` states, and the FR-5.5 answers.

**Dataset removal is a one-way stale.** On removal the exact detections are replaced by bands, which is a lossy mapping — the results were computed from an exact row count that the form no longer holds. There is therefore **no un-stale path** from removal, and the *Un-stale* state does not apply to it. Removing the dataset means the next answer is a re-run. The stale banner says so in that case: `Your inputs changed — re-run to update. (The dataset was removed, so these results can't come back.)`

### Re-run and cache invalidation

The session result cache holds trained models and their computed plots, keyed by `(input snapshot hash, method)`.

- **`Run comparison` reuses the cache** for already-trained methods — but only while the input snapshot is unchanged. That is the only condition under which reuse is correct.
- **Any change to the input snapshot invalidates the entire cache**, immediately, at the moment the change is made — not at re-run time. Cached results answer a different question, and serving them is serving a wrong answer.
- Invalidating the cache does **not** clear the screen. The rendered results stay visible and dimmed under the stale banner; only the reusable-for-training cache is dropped. This is the difference between what the user can read and what the system may re-serve.
- **What survives a re-run:** form answers, expansion states, the set of user-added visualizations (they re-fetch against the new run), the comparison selection, and the series-slot assignments of methods that remain selected. **What is recomputed:** every trained model and every plot, for every method, including the recommended one.
- **What is recomputed on a feature swap:** only the boundary plots. The swap is not in the snapshot, so nothing else is invalidated.
- **Architecture dependency, flagged.** Cache reuse requires server-side per-session retention of the parsed dataset and prior fit results across independent round-trips, in a product with no accounts (NFR-4). This spine asserts a behavior that constrains the architecture, so it says so: the architecture must provide per-session dataset and result retention with a stated TTL. **If the architecture chooses stateless**, `Run comparison` re-trains every method, the estimate line must be derived from the full method count rather than the newly-selected count, and the "already-trained methods are reused" clause is deleted rather than quietly broken.

### Input and detection

| State | Trigger | Treatment | Exit |
|---|---|---|---|
| **Invalid CSV** | File fails extension/MIME/header validation (FR-8.1) | Rejected **before any processing**. Dropzone stays open with an inline `Alert severity="error"`: `This file isn't a CSV we can read. Upload a comma-separated file with a header row.` The form does not change shape; prior answers are untouched. | Dropping a valid file |
| **File too large / too many features** | > 50MB or > 500 features (FR-8.5) | Same treatment, specific message naming **which** limit and the actual value: `This file is 84 MB. The limit is 50 MB.` / `This file has 812 columns. The limit is 500.` Size is checked client-side before the upload begins, so an oversized file never crosses the wire; feature count is checked server-side on the header row, after upload. | Dropping a smaller file |
| **Unsupported column types** | Datetime / text / image columns present (NFR-2) | Do **not** reject the file. Accept it, exclude the unsupported columns from the feature set, and show a `{typography.caption}` under the feature count: `3 columns were skipped — dates and free text aren't supported yet.` with the column names on hover. Rejecting a whole file over one date column would be hostile. If **every** column is unsupported, fall back to the FR-8.1 rejection path. `[ASSUMPTION — the PRD forbids these types but specifies no behavior.]` | — |
| **Degenerate target** | On target selection: the target has 1 unique value; or unique values ≈ row count (an ID column); or, for classification, a class with too few rows to cross-validate | Accept the file; block on the field, the way a missing required field does. Inline message under the target `Select` naming the specific problem: `Every row has the same value in \`status\` — there's nothing to predict. Pick a different column.` / `\`patient_id\` has a different value in almost every row. That looks like an identifier, not something to predict.` / `\`rare_class\` appears in 2 rows — too few to test a model on. Pick a different column or a coarser target.` `Get Recommendation` stays non-interactive until the target changes. Silent nonsense is the worst available outcome here: the detector would happily report "multiclass, 8,000 classes" and train models on it. | User picks another target |
| **Degenerate dataset** | A valid CSV with a header and **zero data rows**, or a single column (no features once a target is chosen) | Same shape as above, on the dropzone rather than the field: `This file has a header row but no data.` / `This file has only one column, so there's nothing to predict from.` | Dropping another file |
| **Low-confidence detection** | Auto-detection confidence below threshold (FR-8.2) | **Per-field, never global.** The field takes a `{colors.status-warning}` icon **and** label (never color alone); its caption changes from `detected from your file` to `We're not sure about this one — please check it.`; the field is marked **unconfirmed**. `Get Recommendation` stays enabled but its `Tooltip` notes how many fields need a look. Any change to the field, or an explicit `Looks right` text button, clears the flag. **Never silently accepted** — the flag persists through re-renders until the user acts on it. | User confirms or edits |
| **Detection failed entirely** | Target column type unresolvable | Prediction type renders **unfilled** with an inline message: `We couldn't tell what kind of prediction this is. Pick one.` and blocks the button like any missing required field. | User picks |

### Scale Guards

NFR-2 permits 500 features and 50MB. Several specified behaviors are physically impossible at those limits, and a guard that is not written down becomes a hang. Every guard below is **stated in the UI**, in the affected panel's `{typography.caption}` or subtitle — a truncation the user cannot see is a lie about the data.

| Surface | Guard | What the UI says |
|---|---|---|
| **Correlation heatmap** | Top-K features by variance, K capped at ~30. In-cell numbers only at K ≤ 20 — below that size the annotation does not fit and the near-zero region recedes into the surface. | `Showing the 30 features with the most variation, of 500.` |
| **Per-feature distributions** | Paginated, with a feature picker. Never 500 panels inside one `Accordion`. | `Showing 12 of 500 features.` plus pagination. |
| **Coefficient plot / feature importance** | Top-20 by magnitude, with a fold. | `Showing the 20 largest, of 500.` |
| **Multiclass faceting** | Hard cap at 6 facets. Above 6 classes, boundary plots are **not rendered at all** rather than rendered uselessly. | `Boundary plots aren't shown above 6 classes — the picture stops being readable.` |
| **Confusion matrix** | In-cell numbers only at ≤ 10 classes; above that the ramp carries magnitude and the text equivalent carries the values. | `Cell values are in the table view — there are too many classes to print them here.` |
| **Tree diagram** | Depth cap, with the depth stated. | `Showing the first 4 levels of 19.` |
| **Scatter forms** | Above a stated point count the form changes (density/hexbin) rather than piling marks, per `DESIGN.md`. | Stated in the subtitle. |

These guards are also a legitimate thesis findings section: *here are the scale limits we found, and here is how the interface degrades at each.* That is a better result than a spec that pretends the limits do not exist.

### Training and results

| State | Trigger | Treatment | Exit |
|---|---|---|---|
| **Incompatible method** | Method invalid for the current prediction type (FR-8.3) | Chip renders `{components.method-chip-disabled}` with its info glyph and a plain-language reason. **Never hidden.** Reason via `Tooltip` in the promoted-3 row; **always inline** in the `Show all methods` list. Focusable, `aria-disabled`, reason as accessible description. | Prediction type changes |
| **Per-method timeout** | Method exceeds its **tiered** timeout — 60s (< 500 rows) / 120s (500–10k) / 300s (> 10k), per FR-8.4, overriding NFR-1's flat 60s | **That method only** is cancelled; the run moves on to the next method. Its column/panels are replaced by a status notice: `Boosting ran out of time on this dataset (5 minute limit). The other methods finished.` **Every other method still displays.** The timed-out method is **excluded** from the FR-5.4 ranking rather than ranked last, with a footnote saying so. `[ASSUMPTION — ranking a timed-out method last would misrepresent it as poor-performing.]` A `Try again` action on the notice retries **that method alone**, and the retry inherits the original run's origin — it is never recorded as a deliberate selection. | Retry or ignore |
| **Partial results** | Some methods resolved, others timed out or errored | The page is fully usable. **No global error state.** The results block header names the reason, not just the count: `4 of 5 finished — 1 timed out.` | — |
| **Stopped by user** | `Stop training` | Finished methods stay. Untrained methods are marked `not trained — you stopped the run` and stay selectable. Header reads `2 of 5 finished — you stopped the run.` Not an error, no `Alert`. | `Run comparison` on the remaining methods |
| **Early halt** | Top 3 within 1 SD after 3 methods (FR-8.4) | **The user is told.** A `{typography.caption}` notice at the top of block 4, phrased as what happened rather than what it implies: `We stopped after 3 methods — the top three scored within one standard deviation of each other, so we didn't train the rest. You can still add them below.` Header reads `Trained 3 methods (stopped early)` — a deliberately different construction from the timeout header, so `3 of 5` never means two opposite things. Not an `Alert` (nothing is wrong), and not silent (an unexplained "only 3" reads as a failure). The remaining candidate methods stay **selectable and enabled** in the comparison selector. | — |
| **Tie in ranking** | Two methods within 1 SD (FR-5.4) | Both rows show `{components.delta-badge-tied}` — the glyph **and the literal word `tied`**, never a number, never color alone. Tied methods sort adjacently and **share a rank number** rather than being arbitrarily ordered. A `{typography.caption}` under the ranking: `Scores within one standard deviation are shown as tied — the difference isn't reliable.` `[ASSUMPTION — shared rank number; FR-5.4 says "shown as tied" without specifying rank display.]` | — |
| **Comparison at cap** | 3 alternatives selected | Unselected **enabled** chips go disabled-with-reason: `You can compare 4 methods at once. Deselect one to swap.` This applies to **every chip on the surface**, including inside `Show all methods` — the cap is a property of the selection, not of the row it is displayed in. Incompatible chips keep their own reason: an incompatibility message always wins over a cap message. | Deselecting one |
| **Backend unreachable** | Network error or 5xx on a dashboard round-trip | An `Alert severity="error"` in place of the loading indicator: `We couldn't reach the server. Nothing was lost — try again.` with a `Try again` action. All form answers and prior results survive untouched. **No auto-retry** — retries are expensive. `[ASSUMPTION — the PRD specifies no network-failure behavior.]` | Retry |

### Benchmark

| State | Trigger | Treatment | Exit |
|---|---|---|---|
| **Benchmark loading** | Page open | `Skeleton` at the heatmap's final dimensions, so the page does not jump. | Data resolves |
| **Benchmark load failure** | The page's own fetch fails | The heatmap region — not the whole surface — is replaced by an `Alert severity="error"`: `We couldn't load the benchmark data. Try again.` with a `Try again` action. The top bar, the page heading, the provenance note, and the FR-6.4 out-of-scope note all still render, so the surface is never a blank screen and the user can still leave via the top bar. | Retry |
| **Benchmark empty** | The benchmark collection returns no rows | The heatmap region shows a plain panel: `No benchmark results are available yet.` Not an `Alert` — an empty benchmark is a state of the project, not an error. | — |
| **Cell hover / focus** | Pointer or keyboard | Tooltip carries **data only**: dataset · source (OpenML-CC18 or UCI, per FR-6.3) · method · score · agree/disagree. No action lives in the tooltip. | — |
| **Report an error — capture** | `Report an error` in a row's header column, or `Enter` on the roving grid cursor | One-level `Dialog`. **Pre-filled, read-only context** (dataset, source, method, score) so the user isn't re-typing what the system knows. One required field — a category `Select`: `the score looks wrong` / `this dataset is mislabelled` / `the agreement marker is wrong` / `something else` — and one optional free-text field carrying the same don't-identify-your-data microcopy as FR-5.5. `[ASSUMPTION — the PRD names the button but specifies no capture fields.]` Focus traps in the dialog and returns to the triggering button on close. `Escape` closes and discards. | Submit or cancel |
| **Report an error — confirmation** | Submit succeeds | Dialog closes. A `Snackbar`: `Thanks — the report is logged.` The reported row takes a persistent `reported` caption for the rest of the session so the user doesn't re-report it. **Nothing else changes** — a report is a note, not an edit to the displayed data. `[ASSUMPTION]` | Session end |
| **Report an error — submit fails** | Network error | Dialog stays open, keeps the typed text, shows an inline `Alert`. **Never discards input on failure.** | Retry |

The Benchmark surface also carries, beneath the heatmap and always: the FR-6.3 provenance note naming both sources and what each covers, and the FR-6.4 note stating that baseline comparisons live in the thesis rather than the UI.

---

## Responsive & Platform

Desktop-first, and honest about what that means. **The page reflows to a single column below 800px; it is never "unsupported".** A layout with a cliff cannot also claim to survive 200% zoom, and the zoom claim is the one that matters for accessibility.

Breakpoints are viewport CSS pixel widths — layout facts, not design tokens.

| Viewport | Comparison columns (block 5) | Method result plots (block 4) | Form | Sticky summary bar |
|---|---|---|---|---|
| **≥ 1416px** | **4 columns.** This is the only range where 4 fit: four panels at `{spacing.plot-min-width}` plus three gaps plus both page margins. | 2-up | Two-column field layout | Sticky |
| **1100–1415px** | **3 columns.** A 4-method comparison wraps the 4th column to a second row of columns, keeping the shared metrics row across all four as a horizontally scrollable strip within its own container. | 2-up | Two-column field layout | Sticky |
| **800–1099px** | **2 columns** | 1-up | Single-column fields | Sticky |
| **< 800px** | **Single column.** Comparison becomes stacked per-method sections in selection order, recommended first. The shared metrics row becomes a stacked metrics table — one row per method, same four quantities — so the numbers stay comparable even when the columns are gone. | 1-up | Single-column fields | Sticky, collapsed to the method name plus `Edit` |

Rules that hold at every width:

- **`{spacing.plot-min-width}` is a hard panel floor at and above 800px, and yields inward below it.** At and above 800px the grid **drops to fewer columns** rather than squashing a panel, and a plot that still cannot reach the floor **wraps to its own row**. Below 800px the panel shrinks to the viewport and the **plot area inside it holds `{spacing.plot-area-min}` and scrolls horizontally within the panel**. This is the one place the floor moves, it moves in exactly one direction, and it is the same rule stated in *Chart Behavior Contract*.
- **The page itself never scrolls horizontally, at any width and any zoom.** This holds independently of the panel floor and is the guarantee the zoom claim actually rests on.
- **The top bar is present at every width** and does not collapse into a menu — it holds two links.
- **Charts with an intrinsic minimum wider than the plot-area floor scroll inside their own panel at every width** — the benchmark heatmap, the correlation heatmap at its cap, wide tree diagrams. Not a narrow-viewport special case.
- **No layout is hidden at any width.** Every block that would render on a wide viewport renders on a narrow one, in the same order.
- **Zoom.** At 200% on a 1440px display the CSS viewport is 720px, which lands in the single-column reflow range and is fully specified. The accessibility claim is therefore stated as **"reflows to a single column, no page-level horizontal scroll"** — which is what 200% zoom needs (WCAG 1.4.4) and what this layout delivers.
- **WCAG 1.4.10 Reflow, stated honestly.** Reflow is measured at 320 CSS px. This product's *page structure* reflows that far, and the panel reflows with it — but the **plot area inside the panel holds `{spacing.plot-area-min}` and scrolls within itself** rather than shrinking to an unreadable width. That is a **partial** conformance to 1.4.10 and is claimed as partial, not as full — see *Accessibility Floor*. It is also the criterion's own allowance for content that requires two-dimensional layout, which charts and data tables are.
- Touch input, orientation change, and print are out of scope for v1 and are not specified here.

---

## Interaction Primitives

**Mouse-first, fully keyboard-operable.** This is a thesis artifact demonstrated on a laptop, not a power-user tool — there is no command palette and no vim-style navigation. The keyboard surface exists because accessibility requires it, not as a speed feature.

- **Click to act.** Every *expensive* state change is an explicit click. **No round-trip fires on hover, focus, or scroll.** Two stated exceptions, both narrow: field validation runs on blur (local, no round-trip), and selecting the target column triggers detection (a round-trip, and the only non-button one in the product — it is the field the entire rest of the form depends on, and making the user click a second button to confirm a choice they just made would be theatre).
- **Hover reveals information, never actions.** Chart tooltips, disabled reasons, skipped-column names. Anything hover-revealed is also reachable by keyboard focus. No action ever lives inside a tooltip — this is why `Report an error` is a persistent row button rather than tooltip content.
- **`Tab` / `Shift+Tab`** — visual order on every surface. The skip link and the two top-bar links come first. Explanation text, captions, and individual chart marks are not tab stops.
- **`Enter` / `Space`** — activate the focused control. `Enter` inside a form field does **not** submit the form.
- **`Escape`** — closes the topmost `Dialog` or `Menu`. Never collapses the form, never cancels a running job. Hover tooltips are not focus-scoped and are not part of the `Escape` stack; they dismiss on pointer-out and on blur.
- **Arrow keys** — inside `RadioGroup`s and `Select` menus (MUI defaults), and inside the **benchmark heatmap**, which is a roving-tabindex 2-D grid: one tab stop for the whole grid, arrows move the cell cursor, `Enter` opens that row's `Report an error`. `[ASSUMPTION — the PRD does not specify heatmap keyboard behavior; a grid of hundreds of cells cannot be N tab stops.]`
- **Accordion** — MUI default. EDA, `Show all methods`, and the per-method result sub-blocks expand on `Enter`/`Space`; their state persists across re-runs.
- **Scroll** — one long page. The collapsed form summary bar is the only sticky element; the top bar is not sticky. No scroll-jacking, no scroll-triggered loading, no parallax.
- **`prefers-reduced-motion`** — honored globally: no chart transitions, no accordion easing, no skeleton shimmer, no dim animation.

**Banned everywhere:**

- Live/reactive recomputation on form change (locked — training is too expensive)
- Drag-and-drop for anything but the file dropzone
- Modal stacks deeper than one level
- Right-click context menus
- Auto-dismissing anything carrying information the user still needs — only the report-confirmation `Snackbar` auto-dismisses
- Confirmation dialogs on non-destructive actions — the one warning that exists is the `beforeunload` guard during a live run, which guards a genuinely destructive event
- Tours, coach marks, first-run overlays, stepper/progress bars implying a sequence — a wizard was rejected upstream, and these are wizards in disguise
- Infinite scroll, or lazy-loading plot panels on scroll
- Toasts for errors that have a home on the page — an error renders where the thing that failed lives
- The real `disabled` attribute on any control whose reason the user needs — `aria-disabled` everywhere, so the reason stays reachable

---

## Accessibility Floor

Behavioral only. Contrast ratios, palette validation, and CVD verification live in `DESIGN.md § Colors` and `§ Data Visualization → Accessibility`.

**Target: WCAG 2.2 AA on both surfaces, with one criterion claimed as partial and named below.**

- **Every interactive element has an accessible name, role, and state.** Disabled method chips, the non-interactive `Get Recommendation` button, and disabled `Add visualization` menu items all use the one contract this file owns and `DESIGN.md` no longer prescribes: **`aria-disabled="true"` + `tabindex="0"` + `aria-describedby`** on the reason — never the `disabled` attribute, never a `<span>` wrapper. They stay focusable, so the reason stays reachable. Full statement in *Component Patterns → Method chip — disabled with reason*.
- **Every form field is programmatically labelled**, and its inline educational explanation is its `aria-describedby`. A screen-reader user gets the education without hunting for it.
- **Low-confidence flags announce.** When detections resolve, an `aria-live="polite"` region announces the count and how many need confirmation. The flag state is exposed per-field programmatically, not only visually.
- **Async state is announced, and throttled.** `aria-live="polite"` fires for: detection complete · **training started (once, with the method count)** · **training finished (once, with the outcome — finished / stopped early / N timed out)** · comparison complete · stale. Per-method progress ticks update the visible text but do **not** each fire an announcement — a screen-reader user should hear two announcements per run, not ten. `aria-live="assertive"` **only** for file rejection and backend failure.
- **Stale announces once**, not per-block: `Results are out of date. Your inputs changed.` The dimming is a visual cue with a text banner behind it — never the sole signal.
- **Color is never the sole carrier**, anywhere: delta direction carries a glyph and, when tied, a word; status carries an icon and a label; train/validation split carries a dash pattern; boundary classes carry a marker shape; confusion-matrix and correlation cells carry their number; benchmark agree/disagree carries a glyph; the method characteristics table carries a word beside its dot count, and the word is the carrier that survives if the dots are ever cut.
- **Every chart has a non-visual equivalent — but "text equivalent" is not the same as "table", and the claim says which is which.** The precise, checkable form, and the only form in which this may be written in the thesis: *every chart container's graphic carries `role="img"` with an `aria-label` naming what it shows and its headline value; and every panel carries a non-visual equivalent — a `View as table` data view for every family except three, and a `View as text` summary for those three.* **The three are the decision boundary, the tree diagram, and the method-selection flowchart**, and they are text summaries because no meaningful table of a prediction raster, a node graph, or a decision path exists — not because they were skipped. The per-family inventory is in *Chart Behavior Contract → Text equivalents, per plot family* and is binding on `DESIGN.md § Table-view form per family`; the two must be changed together. Anything written as a bare "every chart has a table" is false and must not appear in this spec, in the UI, or in the thesis. The `role="img"` goes on the **SVG/canvas only** — not on the panel. Title, subtitle, legend, footnote, and the `View as table` / `View as text` toggle live **outside** it as ordinary content, because `role="img"` makes its subtree presentational and would otherwise hide the fallback from exactly the users it exists for.
- **Direct labelling is the primary relief for `{colors.series-3}` and `{colors.series-4}`**, which sit below the 3:1 mark-contrast floor. The text equivalent is the second channel. This ordering matters: direct labels live in chart code that is being written anyway, so the mitigation survives a scope cut that the text equivalents might not.
- **Focus is visible on every focusable element** and is never removed. Focus order matches reading order on both surfaces.
- **Focus is moved deliberately, never stolen.** On upload success → target column. On results resolve → recommendation panel heading. On error → the error `Alert`. On `Edit` → first form field. On dialog close → the triggering button. Focus is **not** moved while the user is mid-typing or mid-selection, and not while detection is in flight.
- **Dialogs trap focus** and restore it on close (MUI default; do not override).
- **`prefers-reduced-motion`** honored globally.
- **Zoom and reflow.** The page **reflows to a single column below 800px with no page-level horizontal scroll**, which is what 200% browser zoom requires (WCAG 1.4.4) and what the layout in *Responsive & Platform* delivers. **WCAG 1.4.10 Reflow (320 CSS px) is claimed as partial**: page structure reflows and panels reflow with it, but each panel's **plot area** holds `{spacing.plot-area-min}` and scrolls within the panel rather than shrinking below a readable floor. Saying so is the honest position; the alternative is a chart nobody can read, claimed as conformant.
- **No time limits on user input.** The tiered training timeouts bound *server work*, never the user's reading or answering. Nothing on either surface expires.

**Claims that depend on a scope decision** are listed in *Scope Tiers* with the exact sentence that must be deleted if the behavior is cut. An accessibility claim that outlives the feature backing it is worse than never making it.

---

## Inspiration & Anti-patterns

What this product borrows, and what it deliberately refuses. The refusals are locked upstream (addendum § Rejected Alternatives) and are recorded here as a section rather than surviving as inline asides.

**Lifted:**

| Source | What is taken | Why |
|---|---|---|
| **TensorFlow Playground** | The poke-and-see posture: a single page you can prod, where the consequences of a change are visible on the same screen as the change. | It is the reason the form is a top block rather than a wizard — the whole loop is on one surface. |
| **scikit-learn's estimator flowchart / Azure ML cheat sheet** | Decision-path legibility: a recommendation you can follow rather than accept. | Directly the FR-2.2 method-selection flowchart. What is *not* taken is their genericness — this product's flowchart shows the path taken for *this* user's answers. |

**Refused, and why:**

| Anti-pattern | Named in | Why refused |
|---|---|---|
| **AutoML black-box output** (Auto-WEKA, AMLBID) | PRD reference products | A ranked list with no reasoning is the thing this thesis exists to improve on. AMLBID appears here as an evaluation *baseline* (FR-6.4), never as an interaction model. |
| **A step-by-step wizard** | addendum § Rejected Alternatives | Locked. A dashboard "feels more like a playground than a tutorial." Every wizard-shaped affordance is banned by name in *Interaction Primitives* — steppers, tours, coach marks — because they reintroduce the rejected idea in a costume. |
| **Live-reactive recomputation** | addendum § Rejected Alternatives | Locked. Training is too expensive to fire on a keystroke, and a page that recomputes while you think teaches you nothing about which input mattered. |
| **Client-side ML** | addendum § Rejected Alternatives | Locked. All ML is a backend round-trip, which is why every state in this file is an async state. |
| **Hiding incompatible methods** | PRD FR-8.3 as originally written | Overridden per `.memlog.md`: methods that cannot be used stay visible with a plain-language reason. "Why not?" is the most educational question the product can answer. |

**A note the author should read as criticism, not as praise.** The "playground" claim is currently thin: what a user can actually poke without an expensive round-trip is chart tooltips, legend isolation, the text-equivalent toggles, and three accordions. Everything else is *fill the form → click → wait*. Two cheap changes would make the claim true, and neither is in the PRD: a **`Load an example dataset`** button beside the dropzone with two or three pre-parsed classics, and re-framing **advice-only mode as the front door rather than the fallback** — it is the sub-5-second loop, it exercises the rule layer that carries the pedagogy, and it is the only part of the product fast enough to reward poking. Both are listed in *Scope Tiers* as Enhanced. If neither ships, the honest move is to drop the playground language and describe the product as what it is: a deliberate, explicit, non-reactive analysis tool. That is a perfectly good thing to be.

---

## Scope Tiers

This is one student's solo thesis, built alongside a backend, a benchmark study, and a written evaluation. The rest of this document is written in hard rules, which is right for correctness and wrong for planning: a spec with no cut order gets violated silently instead of reduced deliberately. This section is the cut order.

Three tiers. **Core** must ship or the thesis artifact does not demonstrate its own claim. **Enhanced** is real value that can slip. **Deferrable** can be dropped outright — but each Deferrable row names the sentence that must be deleted from this spec and from the thesis if it goes.

### Core — cutting any of these breaks the thesis claim

| Behavior | Why it is Core |
|---|---|
| Problem characterization form, both shapes, with inline explanations under every question | FR-1.6 is the pedagogy. Without it this is a black box with a nicer font. |
| Recommendation panel: primary + fit score + bias-variance + interpretability + key decision factors | FR-2.2's explainable output is the thesis. |
| **Method characteristics table** and the **method-selection flowchart** | The only evidence advice-only mode delivers. Cutting either empties an entire product mode. |
| Advice-only mode | The no-dataset branch is half the PRD's user needs (Practitioner) and the fastest loop in the product. |
| EDA block, collapsed by default | FR-3, and the cheapest visualization work in the product. |
| Model results for the **recommended method** | Without it, "run the recommendation on your data" is not delivered. |
| Disabled-with-reason for incompatible methods | Locked upstream; it is the "nothing is hidden" posture made visible, and it is one of the four Key Flows' climax. |
| Stale = dim + banner, non-destructive | Locked upstream. Cutting it makes the product destructive, contradicting governing posture 2. |
| Benchmark heatmap + provenance + `Report an error` | FR-6 is a formal secondary research objective. |
| **Measurement Behavior** — origin flags, deliberate-selection recording, the FR-5.5 method question | Cutting this returns the acceptance metric to the degenerate 100% it was. This is paperwork and a few logged fields, not UI work: it is the cheapest Core item and the most expensive one to skip. |
| Honest loading estimate + sequential execution + early-halt disclosure | An estimate wrong by 5–25× is the failure mode that makes users reload and lose everything. |
| Direct labelling on charts using `{colors.series-3}` / `{colors.series-4}` | The primary contrast mitigation. Cutting it makes the palette an unmitigated WCAG 1.4.11 failure. |
| `aria-disabled` + reachable reasons, form labelling, focus management, visible focus | Baseline WCAG 2.2 AA. Cutting any of it invalidates the stated conformance target. |

### Enhanced — ship if time allows; cutting costs value, not validity

| Behavior | If cut |
|---|---|
| Model results for **all trained methods** (the collapsed per-method sub-blocks) | Show the recommended method only. Delete "Block 4 renders every method that was actually trained" from the IA and rewrite the block-4 sub-section; the `N of 5 finished` line still works, it just refers to methods whose results live in comparison mode. |
| Comparison mode (block 5) in full | FR-5 is a headline feature; do not cut it lightly. If it goes, the FR-5.4 ranking, the delta badges, the tie treatment, block 6, and Flow 4's climax go with it — and Arm A of the acceptance metric loses its affordance, so the metric drops to Arm B only. Say so in the thesis. |
| `Stop training` | Delete the *Stopped by user* state. The 25-minute ceiling then has no user-side escape, which makes the `beforeunload` guard more important, not less. |
| `Add visualization` (FR-4.4) | Delete the component row, the four library items, the "additive only" rule, and the four chart forms from the chart count. |
| 2-D feature swap (FR-4.3) | Delete the component row and the partial-refetch rule. Boundary plots keep the auto-selected pair. |
| Session-storage answer restore + `beforeunload` guard | Delete the *Page refresh or tab close* state and say plainly in the flows that refresh is a full reset. Do not leave the state in the spec unimplemented. |
| `Load an example dataset` and re-framing advice-only as the front door | Then drop the "playground" language from the Foundation, per *Inspiration & Anti-patterns*. |
| Scale Guards beyond the correlation-heatmap and distribution caps | Those two are the ones that actually hang the tab; the rest degrade gracefully-ish. |

### Deferrable — droppable, with the exact claim that must go

| Behavior | The sentence that must be deleted if it is cut |
|---|---|
| **Un-stale without re-running** | Delete the *Un-stale without re-running* state row and the input-snapshot canonicalization rules that exist only to serve it. Rewrite Flow 3's climax around dim-and-survive, which is already the good part. The snapshot itself stays — cache invalidation still needs it. |
| **Non-visual equivalents on every panel** | If they ship for only some families, **delete the universal sentence in the Accessibility Floor and replace it with the exact list of families that have one**, in both this spec and the thesis. Do not keep the universal claim, and do not restate it as "every chart has a table" — that was never true even at full scope. Direct labelling (Core) remains the contrast mitigation either way. |
| **Per-method streaming render** (panels appearing as each method resolves) | Delete the streaming clause from *Loading — training*, the `N of 5` progress line, and the training-started/finished `aria-live` announcements; replace with a single batch resolve. Flows 1 and 3 lose their progress beats. |
| **Text equivalents for the three summary families** (decision boundary, tree diagram, method-selection flowchart) | These are the three with no meaningful table, so they are the three that cannot be got for free out of the data already in the panel. If they go, the Accessibility Floor sentence must drop from "every panel carries a non-visual equivalent" to the exact list of families that do, in both this spec and the thesis. The flowchart's is the cheapest of the three and is already needed for `View as steps` and for the sub-collapse-width layout — cut it last, or rather do not cut it, since it is the same artifact three times over. |
| **Detection in flight** state | Delete the state row and accept that a large file produces a silent multi-second gap after target selection. Note it as a known rough edge rather than pretending it doesn't exist. |
| **Benchmark empty state** | Only reachable if the benchmark collection is empty, which it will not be by the defense. Safe to skip. |
| **FR-5.5 free-text field** (keeping the two structured questions) | Delete the free-text row and its privacy microcopy. **Do not** cut the `Which method would you use?` question — that one is Core, because Arm A of the acceptance metric is the only strong evidence the thesis has. |

**Rule for using this section:** a cut is legitimate when the corresponding claim is deleted in the same commit. A cut that leaves the claim standing is the failure mode this section exists to prevent.

---

## Key Flows

Four journeys. Every surface in the IA appears in at least one.

### Flow 1 — Marta has a spreadsheet and no idea (Learner)

Marta is a second-year biology master's student. She has a CSV of 340 plant samples and wants to predict whether each one is diseased. She has heard "random forest" in a seminar and nothing else.

1. She opens the dashboard. A top bar with the product name and one `Benchmark` link, then one line of framing text, one dropzone, one form. Nothing is running.
2. She drags `samples.csv` onto the dropzone. It accepts; the dropzone collapses to a filename row.
3. The form switches to Shape A. Only the **target column** `Select` shows. She picks `disease_status`. The field shows a brief progress indicator while the file is scanned, with skeletons standing in for the fields to come.
4. Six properties render below, each captioned `detected from your file`. **Missing value rate** carries a warning icon and reads `We're not sure about this one — please check it.` — her file mixes `NA` with empty strings. She opens the field, sees `some`, clicks `Looks right`. The flag clears.
5. She scrolls to the always-asked questions. Under **non-linearity suspicion** the explanation reads: *Some methods can only draw straight relationships — as one number goes up, the other goes up or down at a steady rate. Others can bend. If you already know the relationship curves, levels off, or flips direction somewhere, say so and we'll prefer a method that can follow it. If you don't know, say so — that's a real answer and we'll treat it as one.* She picks `unsure`, and for once that doesn't feel like failing a quiz.
6. Under **explainability importance**, the explanation says a method she can explain to her supervisor is worth more than a method that scores a fraction higher and can't be described. She picks `critical`.
7. She clicks **Get Recommendation**. The button becomes a spinner: `Training up to 5 methods, one at a time. Each gets at most 1 minute, so the longest this can take is 5 minutes — usually much less, and you'll see each method's results as it finishes.` Skeleton panels appear below.
8. Methods land one at a time. After the third, the count stops and the header reads `Trained 3 methods (stopped early)`. The form collapses to a one-line summary chip. Focus lands on the recommendation heading.
9. **Climax:** the panel says **Logistic Regression**, fit score `0.84`. Beneath it, in a sentence she can actually repeat to her supervisor: *small dataset + interpretability critical → Logistic Regression preferred over Random Forest.* Above the plots sits a quiet line: `We stopped after 3 methods — the top three scored within one standard deviation of each other, so we didn't train the rest. You can still add them below.` The tool didn't only answer her; it told her where its own answer stopped, without pretending that stopping proved anything. She scrolls to a ROC curve she doesn't recognise — and reads its subtitle: *Each point is one cut-off for calling a case positive. Further toward the top-left means the model catches more real positives for fewer false alarms; the diagonal is what you'd get by guessing.*
10. She notices Random Forest is still there in the ranked alternatives, selectable, not hidden. She clicks its chip — a deliberate selection, recorded as one, from the promoted row — then **Run comparison**.

*Failure branch:* her first drag was `samples.xlsx`. The dropzone stayed open: `This file isn't a CSV we can read. Upload a comma-separated file with a header row.` No form appeared, nothing was lost, and she dropped the CSV a second later.

---

### Flow 2 — Diego is checking his own instinct, offline (Practitioner)

Diego is a data analyst with a churn dataset he can't upload to a public tool. He wants a second opinion on his hunch that gradient boosting is overkill.

1. He opens the dashboard and **skips the dropzone entirely**.
2. The form is in Shape B — all banded. He picks: binary classification · `500–10k` rows · `10–50` features · mixed · `some` missing · one class dominates.
3. Explainability `somewhat`. Non-linearity `unsure`. Feature interactions `yes` — and no follow-up field appears, because there's no dataset and therefore no column names to name.
4. **Get Recommendation.** Under five seconds, no estimate line.
5. The recommendation panel fills: primary method with fit score, bias-variance position, interpretability note, key decision factors, the 3 ranked alternatives, the method-selection flowchart, and the **method characteristics table** — his recommended method and the three alternatives across accuracy potential / interpretability / training speed / handles non-linearity / handles missing values, every cell a word he can read off the screen and repeat.
6. The flowchart shows the path his own answers took, with the branches he didn't take still drawn but recessive. He can't click it and doesn't want to; he clicks `View as steps` instead and reads the same path as four conditions in order.
7. Below it there is **no EDA section, no model results, no comparison block, no feedback prompt** — just: `Upload a CSV to see this method run on your data — exploratory plots, model results, and side-by-side comparison unlock with a dataset.`
8. Unconvinced, he clicks **"Where does this come from?"** and lands on the **Benchmark** page.
9. **Climax:** the dataset × method heatmap, rows grouped by source — OpenML-CC18 classification above, UCI regression below — with agreement glyphs marking where the heuristic matched the empirical result and where it didn't. He finds two rows where they disagree, arrows across to a cell, reads the actual score and its source. Beneath the heatmap, one quiet line tells him the baseline comparisons against random selection and AMLBID are in the thesis, not here — the tool is even transparent about what it isn't showing him. He clicks the product title in the top bar and is back on the dashboard, his answers exactly where he left them, trusting it more than the recommendation alone could have earned — not because it agreed with him, but because it showed him where it's wrong.

*Failure branch:* on the benchmark page he spots a score that looks implausible. He clicks **Report an error** in that row — a real button in the row header, not something hiding in a tooltip. The dialog pre-fills dataset, source, method, and score; he picks `the score looks wrong`, types a sentence, submits. `Thanks — the report is logged.` The row now carries a quiet `reported` caption. The heatmap itself doesn't change — his report is a note, not an edit.

---

### Flow 3 — Priya changes her mind three times (Explorer)

Priya found the tool on a forum, has a Kaggle housing dataset open, and no goal beyond seeing what happens.

1. She uploads `housing.csv` — 14,000 rows — and picks `price` as target. Prediction type auto-detects as regression. Class balance never renders.
2. Explainability `not important`. Non-linearity `yes`. Feature interactions `yes` — and because the column-name toggle is on by default, the pair `Autocomplete` pre-populates with `sqft` × `neighborhood`. She adds `year_built` × `condition` herself. The toggle's explanation tells her those names stay in her browser; she believes it, and it happens to be true.
3. **Get Recommendation.** The estimate reads `Training up to 5 methods, one at a time. Each gets at most 5 minutes, so the longest this can take is 25 minutes — usually much less, and you'll see each method's results as it finishes.` She raises an eyebrow at 25 minutes, sees the `Stop training` button next to it, and decides to let it run. As methods finish the ceiling ticks down: `3 methods left, at most 15 minutes.`
4. One method's panel is replaced by a notice: `Boosting ran out of time on this dataset (5 minute limit). The other methods finished.` Everything else rendered. The results header reads `4 of 5 finished — 1 timed out.`
5. She expands the **EDA** accordion — collapsed by default — and gets the correlation heatmap, per-feature distributions, boxplots, target distribution. The heatmap caption says it is showing the 30 features with the most variation, of 68; she'd never have known to ask, and now she doesn't have to.
6. Model results show the recommended method expanded and three more methods as collapsed rows she can open one at a time. She opens two, closes one.
7. She uses **Add visualization** and appends a learning curve. Nothing is removed; the fixed set stays; the menu item is now checked and greyed so she can't add it twice.
8. Then she scrolls back up, clicks **Edit** on the summary bar, and flips non-linearity from `yes` to `no` just to see.
9. **Climax:** the instant she changes the answer, every result below **dims and desaturates but stays completely readable** — the plots she just spent minutes generating are still there, still hoverable, still readable as tables. A banner sits at the top of the region: `Your inputs changed — re-run to update.` Nothing was destroyed by her curiosity. She reads the old residual plot, decides she preferred the previous answer, flips the toggle back — and the dim lifts *without a re-run*, because the inputs match the results again.
10. Idly, she flips the column-name toggle off. **Nothing dims** — it isn't an engine input, and a privacy switch has no business invalidating her plots.

*Failure branch:* she removes the dataset entirely to see what happens. The form reverts to Shape B with her bands carried over from the detections (14,000 rows → `> 10k`) and her always-asked answers intact; the results below go stale rather than vanishing — and the banner is explicit that this one is one-way: `Your inputs changed — re-run to update. (The dataset was removed, so these results can't come back.)` Only when she clicks **Get Recommendation** does the page rebuild in advice-only shape.

---

### Flow 4 — Professor Okonkwo has fourteen minutes and a projector (Instructor)

They teach an applied stats course and want to show, live, why a simple method can beat a complex one.

1. They open the dashboard on the lecture projector with a prepared 300-row CSV — small on purpose, because the small tier caps the whole run at five minutes and fourteen is all they have.
2. Target column picked, detections confirmed, explainability `critical`, non-linearity `no`. **Get Recommendation.** `Each gets at most 1 minute, so the longest this can take is 5 minutes.`
3. The recommendation lands on a linear method. They read the key decision factors aloud — the sentence names the class's own inputs back at them — then put the **method characteristics table** on screen, which says `high` interpretability and `lower` accuracy potential — in words a room can read from the back, with the dot count beside each word for anyone reading it as a shape.
4. They open **Show all methods**. The full list, grouped by area. A student asks about Naive Bayes. It's there — greyed, with an info glyph, and beneath it the inline reason: *Naive Bayes can't be used here — you're predicting a number, and this method only sorts things into categories.* The class can see the method that doesn't apply, **and why**. Nothing was hidden to keep the demo tidy.
5. They select the three most complex compatible methods and click **Run comparison**. Only the comparison block enters loading; the recommendation panel stays on screen for the class to keep reading.
6. **Climax:** the comparison resolves. Across the top, one genuinely aligned row of numbers — CV score with its spread, RMSE, training time, delta % — recommended method leftmost as the reference, showing an em dash where its own delta would be. Below that row each method's own plots run down its own column, at their own heights, with no pretence that a tree diagram and a coefficient plot are the same kind of picture. The ranking below shows `▲ 1.1%` and `▼ 0.4%` — and the third row reading `= tied`, with the word, not a number, under a caption: *scores within one standard deviation are shown as tied — the difference isn't reliable.* The professor doesn't have to explain that a 1% difference on 300 rows is noise. The interface already said it. That is the whole lecture, on screen, in one row.
7. Beneath the ranking, block 6 appears: `Did the results match your expectations?` and `Which method would you use?` — the second one empty, with no answer pre-selected. They ask the room, get an argument, and pick the linear method from the list on the class's behalf. That single click is the only thing in the entire session that counts as accepting the recommendation, and it counts because a person chose it, not because the system trained it.

*Failure branch:* mid-demo the backend drops. The loading indicator is replaced by `We couldn't reach the server. Nothing was lost — try again.` Every form answer and the earlier recommendation are still on screen. They click `Try again` and keep talking.

---

## Coverage Check

**Every IA surface and major affordance is reachable via a Key Flow.** Dashboard (all four) · Benchmark (Flow 2, steps 8–9) · Top bar and return navigation (Flow 2, step 9) · Report an error dialog (Flow 2 failure branchwIKJ) · Method characteristics table (Flow 2 step 5, Flow 4 step 3) · Method-selection flowchart and `View as steps` (Flow 2, step 6) · Add visualization picker (Flow 3, step 7) · Text equivalents (Flow 3, step 9) · Show all methods expander (Flow 4, step 4) · EDA accordion (Flow 3, step 5) · Per-method result sub-blocks (Flow 3, step 6) · Advice-only upload invitation (Flow 2, step 7) · Comparison feedback prompt (Flow 4, step 7) · `Stop training` (Flow 3, step 3, offered and declined).

**Every PRD user need has a delivering surface.** Learner → inline explanation on every question + traceable key decision factors (Flow 1). Practitioner → advice-only mode + method characteristics table + benchmark transparency (Flow 2). Explorer → EDA, additive visualizations, non-destructive stale (Flow 3). Instructor → disabled-with-reason, comparison, tie disclosure (Flow 4).

**Closure notes — reported, not invented:**

1. **The privacy notice (FR-7.4) has a surface but no flow beat.** It is a persistent footer link plus an inline caption under the dropzone, and no protagonist opens it. This is deliberate: a privacy notice that requires a journey to reach is a consent gate, and this product does not gate. Flow 3 step 2 touches its *substance* — the column-name toggle's explanation — without opening the dialog. Flagged rather than fabricated.
2. **FR-2.4's behavioral satisfaction measurement has no rendered surface, but it was previously reported here as "Not a gap." That was false and is corrected.** The metric as the PRD defines it is degenerate: FR-8.4 auto-trains the top methods by fit score, so the recommended method is always trained and "did the user run the recommended method" always reads true. The fix is in *Measurement Behavior* — acceptance is recorded on deliberate user choice only, system-initiated runs never count, and the affordance that makes an explicit choice possible is the FR-5.5 prompt's second question. This is a change to the PRD's Success Metrics section and to FR-7.3, not a UI detail.
3. **FR-5.5 is now fully in the IA** — block 6 of the Dashboard block-order table, a Component Patterns row with its submit / confirm / failure triad, and a beat in Flow 4 step 7 where a protagonist actually answers it. The earlier claim that it was "in the IA" was false when written; it is true now.
4. **FR-6.4 (Random-selection and AMLBID baselines) has no UI surface, deliberately and visibly.** It is a thesis-report deliverable. The Benchmark surface states this on the page rather than leaving a silent absence, and Flow 2 step 9 has a protagonist read it.
5. **FR-6.3 (dataset provenance) is mapped**: source appears as row-group headers on the benchmark heatmap and in the cell tooltip.
6. **NFR-3's browser list is recorded in the Foundation** and appears in no flow, because a browser list is a constraint rather than an experience.
7. **The 25-minute worst case is real and is not hidden.** The product's answer to it is an honest ceiling that ticks down, per-method streaming so the wait is legible, `Stop training` so it is escapable, and a `beforeunload` guard so it is not lost by accident. There is no version of sequential training with early halt that makes the ceiling small; pretending otherwise was the previous draft's actual defect.
