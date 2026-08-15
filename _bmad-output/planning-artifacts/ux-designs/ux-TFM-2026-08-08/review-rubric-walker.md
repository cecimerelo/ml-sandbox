# Rubric Walker Review — TFM Recommender

- **DESIGN.md:** `/Users/cecimerelo/Desktop/personal/TFM/_bmad-output/planning-artifacts/ux-designs/ux-TFM-2026-08-08/DESIGN.md`
- **EXPERIENCE.md:** `/Users/cecimerelo/Desktop/personal/TFM/_bmad-output/planning-artifacts/ux-designs/ux-TFM-2026-08-08/EXPERIENCE.md`
- **Lens:** systematic coverage check (section completeness · token integrity · separation of concerns · IA closure · state coverage · undefined behavior)
- **Run at:** 2026-08-08

---

## Verdict

**Conditional pass — strong spine, six holes a developer cannot build through.** Token integrity is perfect (0 broken references across 67 distinct citations), separation of concerns is near-perfect in one direction (EXPERIENCE.md contains zero hex codes, px values, opacities, or type sizes), and state coverage against PRD-named states is complete with every transition trigger populated. The failures are all *absence*, not error: three artifacts the PRD explicitly requires (FR-2.2 method-selection flowchart, FR-2.2 static comparison table, FR-5.5 feedback prompt) have no spec in either file, the central Model results block never says what it contains, and the responsive contract both goes unwritten and contradicts the Accessibility Floor's 200%-zoom claim. One self-assessment in the Coverage Check is factually wrong.

**Category verdicts**

| Category | Verdict |
|---|---|
| Section completeness | adequate (2 required-when-applicable sections missing) |
| Token integrity | **strong** (0 broken) |
| Separation of concerns | adequate (clean one way; DESIGN.md leaks behavior) |
| IA closure | thin (2 unmapped FRs, 1 unreachable surface, 1 false claim) |
| State coverage | **strong** (all PRD states specified, all triggers named) |
| Undefined behavior | thin (6 blocking guesses) |

Counts: **6 Blocker · 11 Should-fix · 10 Nit**

---

## 1. Section completeness

**DESIGN.md** — canonical order is `Brand & Style → Colors → Typography → Layout & Spacing → Elevation & Depth → Shapes → Components → Do's and Don'ts`. Actual: Brand & Style → Colors → Typography → Layout & Spacing → Elevation & Depth → Shapes → Components → **Data Visualization** → Do's and Don'ts. All eight canonical sections present, non-empty, in order. `Data Visualization` is an invented section inserted before the order-locked terminal section; it is the largest and most load-bearing section in the file and unambiguously earns its place. **PASS.**

**EXPERIENCE.md** — all eight required defaults present and in relative order: Foundation → Information Architecture → Voice and Tone → Component Patterns → [The Problem Characterization Form] → [The Explanation Layer] → [Chart Behavior Contract] → State Patterns → Interaction Primitives → Accessibility Floor → Key Flows → [Coverage Check]. Four invented sections, all substantive. **PASS on required defaults.**

**Missing required-when-applicable:**
- **Responsive** — triggered (DESIGN.md defines breakpoint behavior at 1200px/900px; Foundation says "desktop-first responsive web"). See Blocker B5.
- **Inspiration & Anti-patterns** — triggered. `addendum.md § Rejected Alternatives` names three rejects (wizard, live-reactive, client-side ML) and the PRD names five reference products (TensorFlow Playground, Decision Boundary Playground, Auto-WEKA, AMLBID, sklearn flowchart / Azure ML cheat sheet). The rejects appear scattered as inline asides ("a wizard was rejected upstream"); the reference products appear nowhere. See Should-fix S7.

**Visual reference coverage:** `imports/` is empty; no `mockups/` or `wireframes/` directories exist. No orphans, no unspecific references. **N/A.**

---

## 2. Token integrity — full results

Extracted all 162 frontmatter key paths from DESIGN.md and all `{path.to.token}` citations in both files.

### EXPERIENCE.md → DESIGN.md (21 distinct citations, 34 occurrences)

| Reference | Uses | Resolves |
|---|---|---|
| `{colors.series-1}` | 2 | ✅ |
| `{colors.series-4}` | 1 | ✅ |
| `{colors.series-other}` | 1 | ✅ |
| `{colors.status-warning}` | 1 | ✅ |
| `{components.delta-badge-up}` | 1 | ✅ |
| `{components.delta-badge-down}` | 1 | ✅ |
| `{components.delta-badge-tied}` | 2 | ✅ |
| `{components.fit-score-meter}` | 2 | ✅ |
| `{components.form-summary-bar}` | 2 | ✅ |
| `{components.method-chip}` | 1 | ✅ |
| `{components.method-chip-disabled}` | 2 | ✅ |
| `{components.plot-panel}` | 1 | ✅ |
| `{components.stale-results}` | 1 | ✅ |
| `{spacing.plot-aspect}` | 1 | ✅ |
| `{spacing.plot-min-width}` | 1 | ✅ |
| `{spacing.section-gap}` | 1 | ✅ |
| `{typography.body}` | 2 | ✅ |
| `{typography.body-educational}` | 3 | ✅ |
| `{typography.caption}` | 7 | ✅ |
| `{typography.chart-subtitle}` | 2 | ✅ |
| `{path.to.token}` | 1 | — *(literal syntax illustration, EXPERIENCE.md:24 — not a reference; **not a defect**)* |

**Broken references: 0.**

### DESIGN.md prose → DESIGN.md frontmatter (46 distinct citations, 84 occurrences)

All 46 resolve. **Broken references: 0.** Spot-checked the full list: `colors.*` (27), `rounded.*` (3), `spacing.*` (7), `typography.*` (9). No typos, no orphaned paths, no case mismatches.

### Defined-but-never-cited (informational, not defects)

Ramp interior steps (`seq-200/300/400/500/600`, `div-neg-100/300/500/700`, `div-pos-100/300/500/700`) are defined but cited only as ramp endpoints in prose — correct and expected for a ramp. `colors.background-default`, `colors.chart-ink`, `rounded.DEFAULT`, `spacing.unit` likewise. Component sub-keys are cited at the component level (`{components.plot-panel}`), which is the intended granularity.

**One genuine naming defect:** `typography.h1` and `typography.h2` are defined in frontmatter but the Typography prose calls the same roles `h4` and `h6` (their MUI names), and neither spine ever cites `{typography.h1}` / `{typography.h2}`. See Nit N1.

---

## 3. Separation of concerns

### EXPERIENCE.md → DESIGN.md leakage: **none found.**

Grepped for hex codes, `px`/`rem`/`em`/`pt` values, `opacity`, `saturate`, `rgba`, and the literal magnitudes used in DESIGN.md (1440, 1200, 900, 320, 68ch, 8px, 4px, 2px). **Zero hits** other than the Foundation sentence declaring the rule and one narrative use of the word "desaturates" in Flow 3. This is exemplary.

### DESIGN.md → EXPERIENCE.md leakage: **five sites**, all duplicating rules EXPERIENCE.md also owns. See Should-fix S5.

---

## 4. IA closure

### 4a. Surface → Key Flow reachability

| IA surface | Reached in flow |
|---|---|
| Dashboard | Flows 1–4 ✅ |
| Benchmark | Flow 2 step 7 ✅ |
| Report an error dialog | Flow 2 failure branch ✅ |
| Add visualization picker | Flow 3 step 6 ✅ |
| View as table | Flow 3 step 8 ✅ |
| **Privacy notice** | **none** — self-flagged in Coverage Check note 1 with a defensible rationale. Nit N5. |

### 4b. FR → surface traceability

| Req | Delivering surface / section | Status |
|---|---|---|
| FR-1.1 | EXP § The Problem Characterization Form → *Shape: adaptive on dataset presence* | ✅ |
| FR-1.2 | EXP § Shape A (fields 1–8) + *Auto-detect confirm row* | ✅ |
| FR-1.3 | EXP § Shape B | ✅ |
| FR-1.4 | EXP § Always asked (fields 9–11) | ✅ (answer type for interactions is an `[ASSUMPTION]` filling a real PRD gap) |
| FR-1.5 | EXP § Column-name opt-in | ✅ |
| FR-1.6 | EXP § Component Patterns → *Form field + inline explanation*; § The Explanation Layer | ✅ |
| FR-1.7 | EXP § Component Patterns → *`Get Recommendation` button* | ✅ |
| FR-2.1 | Engine-internal; no UI required. Layer-1-vs-empirical agreement surfaces on Benchmark. | ✅ |
| FR-2.2 — primary rec + fit score | DESIGN § Fit score meter; EXP § Component Patterns | ✅ |
| FR-2.2 — ranked alternatives | EXP § IA (recommendation panel contents) | ✅ |
| FR-2.2 — bias-variance position | EXP § The Explanation Layer | ✅ |
| FR-2.2 — interpretability note | EXP § The Explanation Layer | ✅ |
| FR-2.2 — key decision factors | EXP § The Explanation Layer | ✅ |
| FR-2.2 — **method selection flowchart** | **named in one IA list item; specified nowhere** | ❌ **B1** |
| FR-2.2 — **static comparison table** | **named in IA list + Flow 2; specified nowhere; name collides with FR-5.3's table** | ❌ **B2** |
| FR-2.3 | EXP § Voice and Tone; § The Explanation Layer → *Citation-free* | ✅ |
| FR-2.4 | Deferred to v2; no surface, explicitly reported in Coverage Check note 2 | ✅ (correctly reported) |
| FR-3.1 | EXP § Dashboard block order, block 3 *Present when* | ✅ |
| FR-3.2 | EXP block 3 *Collapsible*; § Interaction Primitives → Accordion | ✅ |
| FR-3.3 — histogram / correlation heatmap / boxplot / target distribution | DESIGN § Data Visualization → *EDA* family | ✅ |
| FR-3.3 — **bar chart for categorical features** | **not in the EDA family row** | ⚠️ **S3** |
| FR-4.1 | EXP § State Patterns → *Full results* | ✅ |
| FR-4.2 (all 15 method rows) | DESIGN § Data Visualization → 10 plot families; all 20 named plot types covered | ✅ |
| FR-4.3 | EXP § Component Patterns → *2-D projection feature swap* | ✅ |
| FR-4.4 | EXP § Component Patterns → *`Add visualization` control* (library matches PRD verbatim) | ✅ |
| FR-5.1 | EXP § Component Patterns → *Method chip* (cap of 3 alternatives) | ✅ |
| FR-5.2 | EXP § *`Run comparison` button*; DESIGN § Comparison table | ✅ |
| FR-5.3 | DESIGN § Comparison table; EXP § Component Patterns → *Comparison table* | ✅ |
| FR-5.4 | EXP § State Patterns → *Tie in ranking*; DESIGN § Delta badge | ✅ |
| FR-5.5 | **narrative mention only (Flow 4 step 7); no IA row, no component row, no state row** | ❌ **B3** |
| FR-6.1 | EXP § IA → Benchmark | ✅ |
| FR-6.2 | DESIGN § Benchmark heatmap; EXP § *Benchmark heatmap cell*, *`Report an error` button* | ✅ |
| FR-6.3 (OpenML-CC18 / UCI provenance) | **no surface displays dataset provenance** | ⚠️ **S2** |
| FR-6.4 (Random-selection & AMLBID baselines) | **no surface; not flagged in Coverage Check either** | ⚠️ **S1** |
| FR-7.1 | Backend; implied by "nothing expensive is reactive" posture | ✅ |
| FR-7.2 | EXP § Component Patterns → *Privacy notice* | ✅ |
| FR-7.3 | Backend; no UI required | ✅ |
| FR-7.4 | EXP § IA → Privacy notice (footer link + inline caption + Dialog) | ✅ (Dialog content unspecified — N-level) |
| FR-8.1 | EXP § State Patterns → *Invalid CSV* | ✅ |
| FR-8.2 | EXP § State Patterns → *Low-confidence detection*, *Detection failed entirely* | ✅ |
| FR-8.3 | EXP § State Patterns → *Incompatible method* (deliberate memlog-locked override to disabled-with-reason; PRD patched per memlog) | ✅ |
| FR-8.4 | EXP § State Patterns → *Per-method timeout*, *Early halt*, *Partial results* | ✅ |
| FR-8.5 | EXP § State Patterns → *File too large / too many features* | ✅ |
| NFR-1 | EXP § *Loading — advice only* (no estimate, <5s) / *Loading — training* (tiered estimate); flat-60s overridden per memlog | ✅ |
| NFR-2 | EXP § *Invalid CSV*, *File too large*, *Unsupported column types* | ✅ |
| NFR-3 — no mobile | EXP § Foundation | ✅ |
| NFR-3 — **Chrome/Firefox/Safari/Edge** | **named nowhere in either spine** | ⚠️ **N8** |
| NFR-4 | EXP § Foundation (no auth, no accounts, session = one tab); Privacy notice | ✅ |

**Unmapped: FR-2.2 (flowchart), FR-2.2 (static comparison table), FR-5.5, FR-6.3, FR-6.4, NFR-3 (browser list), FR-3.3 (categorical bar chart).**

---

## 5. State coverage

Every state named in the PRD has a specified behavior, and every row in EXPERIENCE.md's three State Patterns tables carries a populated Trigger column. Verified state-by-state:

- FR-8.1 invalid CSV ✅ · FR-8.2 low-confidence ✅ + detection-failed ✅ · FR-8.3 incompatible ✅ · FR-8.4 timeout ✅ / early halt ✅ / partial ✅ · FR-8.5 size + feature limits ✅ · FR-3.2 collapsed-by-default ✅ · NFR-1 loading (both tiers) ✅ · NFR-2 unsupported column types ✅
- States invented beyond the PRD and correctly triggered: initial/empty, advice-only, stale, **un-stale-without-re-running**, re-running-from-stale, comparison-running, comparison-at-cap, backend-unreachable, benchmark loading, report-capture / confirmation / submit-failure.

**Verdict: strong.** Gaps are missing *surfaces* (§4) and missing *degenerate-input* cases (S11), not missing state behavior.

---

## Findings

### Blocker (6)

**B1 — Method-selection flowchart (FR-2.2) has no spec in either file.**
*File:* both. *Section:* EXPERIENCE.md § Information Architecture (recommendation panel contents list); DESIGN.md § Data Visualization.
The flowchart is named once, in a comma-list of panel contents, and never again. DESIGN.md's ten plot families cover ~25 chart types; none is a flowchart (§ *Structure* covers tree diagrams only, which is a different object with different semantics). A developer must invent: static image vs. rendered graph, node/edge visual language, whether the user's actual path is highlighted, whether nodes are interactive, how it behaves at `{spacing.plot-min-width}`, and whether it has a `View as table` equivalent.
*Fix:* add a **Decision flowchart** row to DESIGN.md § Data Visualization → *Slot assignment by plot family* (proposed: nodes on `{colors.background-paper}` with `{colors.divider}` borders and `{colors.chart-ink}` text, matching the *Structure* family; the user's traversed path in `{colors.series-1}` at 2px, untraversed edges in `{colors.chart-axis}` dashed) and a one-line behavioral contract in EXPERIENCE.md § Component Patterns (proposed: static, non-interactive, `role="img"` with an `aria-label` restating the path in prose, plus the mandatory `View as table` rendering the path as an ordered list of conditions).

**B2 — Static comparison table (FR-2.2) has no spec, and its name collides with the FR-5.3 comparison table.**
*File:* both. *Section:* EXPERIENCE.md § IA (panel contents), Flow 2 step 5; DESIGN.md § Components → *Comparison table*.
Two different tables exist in this product: the **static qualitative** table (recommended vs. alternatives across accuracy potential / interpretability / training speed / handles non-linearity / handles missing values — available with *or without* a dataset) and the **empirical** comparison table (column-per-method, CV score, `{typography.metric-value}`, `series-N` dots — dataset-only). DESIGN.md § Components → *Comparison table* specifies only the second. The first has no cell-rendering rule at all: are qualitative values words ("high"/"medium"/"low"), rating dots, check/cross glyphs, or a filled meter? This is the *only* evidence artifact advice-only users get, so it is load-bearing for an entire product mode.
*Fix:* rename DESIGN.md § Components → *Comparison table* to **Empirical comparison table**, add a sibling **Method characteristics table** section specifying the qualitative cell encoding, and disambiguate both names everywhere in EXPERIENCE.md.

**B3 — FR-5.5 feedback prompt is unspecified, and the Coverage Check makes a false claim about it.**
*File:* EXPERIENCE.md. *Section:* § Coverage Check, closure note 3; § Information Architecture; § Component Patterns; § State Patterns.
Note 3 states: *"FR-5.5's post-comparison feedback prompt is in the IA and appears in Flow 4 step 7."* It is **not in the IA** — neither the surface table (6 rows) nor the Dashboard block-order table (6 blocks) contains it. It exists only as a single line of Flow 4 narrative. Undefined: the control type for the free-text comment, whether the yes/no answer is required, submit trigger, success confirmation, submit-failure behavior, whether it persists per session, and whether it re-appears after a second `Run comparison`. FR-7.3 requires the response to be stored linked to the session record, so this is a real backend contract with no front-end spec.
*Fix:* correct note 3 to say the prompt is *not* in the IA, then add it — a row in § Component Patterns (behavioral contract, mirroring the *Report an error* dialog's submit/confirm/fail triad) and rows in § State Patterns for submitted / submit-failed. Reuse the `Snackbar` confirmation pattern already established for error reports.

**B4 — The Model results block (block 4) never says what it contains.**
*File:* EXPERIENCE.md. *Section:* § Information Architecture → Dashboard block order, row 4.
FR-8.4 trains up to 5 methods; FR-2.2 surfaces 1 primary + 3 ranked alternatives; FR-4.2 assigns 2–3 fixed plots per method. Block 4 is described only as "Model results / Only when a dataset is uploaded, after training resolves." Nothing states whether it renders plots for **the recommended method alone**, **all trained methods**, or **the primary + 3 alternatives**. The states table implies the second (`4 of 5 methods finished`, "each method's panels render the moment that method resolves", "A method's panels appear together"), but implication is not specification — and the difference is 2–3 panels versus ~13, which changes the entire page layout, the 2-up grid math in DESIGN.md § Layout & Spacing, and the relationship between block 4 and block 5.
*Fix:* add an explicit sub-section under § Information Architecture stating block 4's composition — proposed: one titled sub-block per trained method, in fit-score-descending order, each carrying that method's FR-4.2 fixed plot set at 2-up, with the recommended method's sub-block first. Also state how block 4 relates to block 5 (block 5 re-renders the same plots in column-per-method form for the selected subset).

**B5 — Responsive behavior is unwritten and contradicts the Accessibility Floor.**
*File:* both. *Section:* DESIGN.md § Layout & Spacing (`{spacing.content-max}` assumption); EXPERIENCE.md § Accessibility Floor (200% zoom bullet); EXPERIENCE.md — no Responsive section.
DESIGN.md declares "below a 1200px viewport, comparison drops to 2 columns × 2 rows; **below 900px the layout is unsupported**." EXPERIENCE.md then claims "**The page works at 200% browser zoom** — the desktop-first layout reflows rather than requiring horizontal scroll." At 200% zoom on a 1440px display the CSS viewport is 720px — *below the 900px unsupported floor*. Both statements cannot be true. Separately, "unsupported" has no defined behavior: horizontal scroll, a blocking message, or nothing at all? And EXPERIENCE.md has no Responsive section at all, so the *behavior* at the 1200px break (does the sticky summary bar survive? does the comparison column order change? does row-alignment survive the 2×2 wrap?) is entirely undefined.
*Fix:* add a **Responsive & Platform** section to EXPERIENCE.md with a breakpoint table (≥1200 / 900–1200 / <900) naming the behavior of the plot grid, comparison columns, and sticky summary bar at each. Then reconcile the zoom claim — either raise the floor's honesty (state that 200% zoom degrades to the 900–1200 layout and that below 900px the page scrolls horizontally rather than breaking), or drop the "no horizontal scroll" assertion. WCAG 1.4.10 reflow is measured at 320px CSS width, which this product will not meet; say so deliberately rather than claiming otherwise.

**B6 — The persistent top bar exists in the IA with zero spec, and return navigation from Benchmark is undefined.**
*File:* both. *Section:* EXPERIENCE.md § Information Architecture (the `[ASSUMPTION]` block); DESIGN.md § Elevation & Depth.
The IA introduces "a persistent top bar with the product title on the left and a single `Benchmark` text link on the right." Nothing else in either spine mentions it: no `AppBar` entry in DESIGN.md § Components (no height, elevation, sticky behavior, or background), no row in EXPERIENCE.md § Component Patterns, no place in the Dashboard block-order table (which starts at the form). It also **contradicts** DESIGN.md § Elevation & Depth: *"Elevation 1 — the collapsed form-summary bar … and the stale-results banner. **These are the only two elements that sit above the page plane.**"* A persistent top bar is a third. Most concretely: **how does a user get back to the Dashboard from Benchmark?** Flow 2 step 8 says "He goes back to the dashboard" with no mechanism. The Benchmark surface's IA row lists what it is reached *from*, never what it returns *to*.
*Fix:* add an `app-bar` entry to DESIGN.md `components` frontmatter and a short § Components sub-section (proposed: `AppBar position="sticky" elevation={0}` on `{colors.background-paper}` with a `{colors.divider}` bottom hairline — which resolves the elevation contradiction rather than creating a third floating element); add a row to EXPERIENCE.md § Component Patterns stating that the product title is a link to `/` and is the return path from Benchmark; add the top bar as block 0 in the Dashboard block-order table and note it is present on both surfaces.

---

### Should-fix (11)

**S1 — FR-6.4 (Random-selection and AMLBID baselines) is unmapped and unflagged.**
*File:* EXPERIENCE.md § Information Architecture / § Coverage Check.
FR-6.4 sits inside FR-6 "Benchmark Transparency Page" and names two comparison baselines. Neither spine mentions them. This may legitimately be thesis-only (a research objective, not a UI requirement) — but the Coverage Check explicitly flags FR-2.4 and FR-5.5 as non-surfaces and stays silent here, so a downstream consumer cannot tell whether it was considered or missed.
*Fix:* either add a baselines panel to the Benchmark IA (recommender vs. random vs. AMLBID on top-1 hit rate / regret / Spearman ρ — the PRD's own Research Metrics) or add a fourth closure note stating FR-6.4 is a thesis-report deliverable with no v1 UI.

**S2 — FR-6.3 benchmark provenance has no surface.**
*File:* EXPERIENCE.md § Information Architecture → Benchmark; DESIGN.md § Benchmark heatmap.
The page's entire purpose is transparency, and the heatmap's rows are datasets — but nothing says whether a row identifies its source (OpenML-CC18 vs. UCI). The hover tooltip is specified as "dataset · method · score · agree/disagree · Report an error"; source is absent.
*Fix:* add source to the cell tooltip and/or a row-group header splitting classification (OpenML-CC18) from regression (UCI).

**S3 — FR-3.3's categorical bar chart is missing from DESIGN.md's EDA family.**
*File:* DESIGN.md § Data Visualization → *Slot assignment by plot family*, EDA row.
FR-3.3 requires "histogram for numeric, **bar chart for categorical**." The EDA row lists "histogram, boxplot, target distribution" plus the correlation heatmap. A categorical bar chart has different needs (category ordering, long-label handling, "Other" folding into `{colors.series-other}`).
*Fix:* add it to the EDA row, state the sort (frequency-descending) and the `series-other` fold rule for high-cardinality columns.

**S4 — No rule for series-slot assignment after a deselect-then-select.**
*File:* EXPERIENCE.md § Chart Behavior Contract → *Color follows the entity, not the rank*.
The spine states alternatives take slots 2/3/4 in selection order, and that **a freed slot is not backfilled**. But the cap is 3 alternatives. If a user deselects the slot-2 method and selects a new one, the new method needs a slot — and under strict no-backfill there is no slot 5. The rule is self-defeating at the cap.
*Fix:* state the resolution explicitly — proposed: no-backfill applies only while a session's *existing* selections are stable; a newly selected method takes the lowest free slot (which is the freed one), and only *already-rendered* methods are guaranteed not to repaint.

**S5 — DESIGN.md specifies behavior in five places, duplicating EXPERIENCE.md.**
*File:* DESIGN.md.
Sites: § Elevation & Depth (hover border-color change); § Components → *Method chip* (tooltip-on-hover/focus placement rule, `<span>` wrap, `aria-disabled` + accessible description); § Components → *Stale results* ("per-plot controls go `disabled`"); § Components → *Benchmark heatmap* ("Cell hover shows dataset, method, score, and the Report an error affordance"); § Data Visualization → **Interaction** (entire sub-section: hover layers, crosshair vs. per-mark tooltips, hit-target sizing, click-to-isolate legends, control-row placement) and § Accessibility (`View as table` toggle behavior). Every one of these is also specified in EXPERIENCE.md, mostly as a superset. No contradictions today, but two sources of truth for the same rule is a drift risk and violates the spine contract stated in EXPERIENCE.md:24.
*Fix:* in DESIGN.md, keep only the *visual* residue (tooltip elevation and radius, swatch/typography inside the tooltip, hit-target *size* as a visual floor, the hover border-color token pair) and replace the behavioral sentences with a pointer to `EXPERIENCE.md § Chart Behavior Contract`. The `aria-*` prescriptions in § Components → *Method chip* belong wholly in EXPERIENCE.md § Accessibility Floor, where they already appear.

**S6 — DESIGN.md frontmatter has no `sources` key.**
*File:* DESIGN.md frontmatter.
EXPERIENCE.md declares four sources (prd.md, addendum.md, .memlog.md, DESIGN.md); DESIGN.md declares none. Inheritance is unverifiable from the file itself.
*Fix:* add `sources:` listing `../../prds/prd-TFM-2026-07-26/prd.md`, `.../addendum.md`, and `./.memlog.md`.

**S7 — Missing Inspiration & Anti-patterns section.**
*File:* EXPERIENCE.md.
Triggered by both the addendum's Rejected Alternatives and the PRD's five named reference products. The rejects currently survive as inline asides that a reader could mistake for editorializing ("a wizard was rejected upstream, and these are wizards in disguise"), and the reference products — the direct competitive frame for the whole thesis — appear nowhere.
*Fix:* add the section between § Accessibility Floor and § Key Flows: what is lifted (TensorFlow Playground's poke-and-see posture; the sklearn flowchart's decision-path legibility), what is explicitly rejected (AutoML black-box output à la Auto-WEKA/AMLBID; the step-by-step wizard; live-reactive recomputation; client-side ML), each with the one-line reason.

**S8 — The Benchmark surface has no error state, no empty state, and no legend spec.**
*File:* EXPERIENCE.md § State Patterns → Benchmark; DESIGN.md § Benchmark heatmap.
Only *Benchmark loading* is specified. The *Backend unreachable* row is scoped generically ("any round-trip") but its treatment is dashboard-shaped ("an `Alert` in place of the loading indicator"), which does not describe a whole page failing to load. Separately, a sequential-ramp heatmap with glyph overlays needs a **legend** — for the `seq-100`→`seq-700` scale and for the ✓/✗ agreement markers — and neither spine specifies one.
*Fix:* add Benchmark load-failure and (if reachable) empty rows to the Benchmark state table; add a legend to DESIGN.md § Benchmark heatmap anatomy.

**S9 — "`View as table` never changes panel height enough to reflow the grid above it" has no mechanism.**
*File:* EXPERIENCE.md § Component Patterns → *Plot panel*.
This is a hard constraint with no implementation path. A 5-series × 40-point table is far taller than a 4:3 chart. Does the table scroll inside a fixed-height panel? Truncate with a "show all" affordance? Paginate?
*Fix:* state it — proposed: the table renders inside the panel at the chart's exact `{spacing.plot-aspect}` box with internal vertical scroll and a sticky header row.

**S10 — Re-run cache semantics are undefined.**
*File:* EXPERIENCE.md § Component Patterns → *`Run comparison` button*; § State Patterns → *Re-running from stale*.
`Run comparison` correctly specifies cache reuse for already-trained methods. But `Re-run` from stale fires "the same pipeline as `Get Recommendation`" after the *inputs changed* — which should invalidate the cache entirely, since cached results answer a different question. Never stated. A developer reading only the `Run comparison` row would plausibly reuse the cache and serve wrong results.
*Fix:* add one sentence to *Re-running from stale*: any change to the input snapshot invalidates the whole session result cache; `Run comparison` reuse applies only when the input snapshot is unchanged.

**S11 — Degenerate CSVs fall outside every specified rejection path.**
*File:* EXPERIENCE.md § State Patterns → Input and detection.
Covered: bad extension/MIME/header, >50MB, >500 features, unsupported column types. Not covered: a valid CSV with a header row and **zero data rows**; a **single-column** CSV (no features once the target is chosen); a target column of all-unique values (an ID column, which would auto-detect as high-cardinality multiclass and produce nonsense).
*Fix:* add a *Dataset too degenerate to model* row — proposed treatment: accept the file, but on target selection show an inline message under the target `Select` naming the specific problem and block `Get Recommendation` the way a missing required field does.

---

### Nit (10)

**N1** — `typography.h1` / `typography.h2` are defined in DESIGN.md frontmatter but § Typography prose names the same roles `h4` and `h6` (their MUI names), and neither spine ever cites the tokens. Two names for one role. *Fix:* rename the frontmatter keys to `page-title` and `section-heading` (or to `h4`/`h6` to match MUI), and cite them from § Typography.

**N2** — `{path.to.token}` at EXPERIENCE.md:24 is the only string matching token syntax that does not resolve. It is a deliberate syntax illustration, **not a defect**; recorded here so a future automated check does not re-flag it. *Fix (optional):* escape it as `` `{path.to.token}` `` inside a code fence, or write it as `{…}`.

**N3** — § Coverage Check enumerates "Show all methods expander," "EDA accordion," and "Advice-only upload invitation" as IA surfaces reached by flows, but none is a row in the § Information Architecture table. *Fix:* either add them to the IA table or reword the Coverage Check to say "surfaces and major affordances."

**N4** — § Foundation says "Two surfaces only," while the § Information Architecture table has six rows. Consistent once you read the table's mix of surfaces/modals/toggles, but the count clashes on first read. *Fix:* split the IA table into *Surfaces* (2) and *Overlays & in-place toggles* (4).

**N5** — The Privacy notice is the one IA row no Key Flow reaches. Self-flagged with a defensible rationale (closure note 1). Recording it for completeness only; no fix required.

**N6** — § Validation and enablement specifies "The disabled button carries a `Tooltip` naming what's missing." MUI `Tooltip` does not fire on a `disabled` button — the `<span>` wrap workaround is documented for the disabled *chip* but not for this button. *Fix:* apply the same note here, or use `aria-disabled` on the button as the chips do.

**N7** — DESIGN.md carries two Do's-and-Don'ts tables (§ Data Visualization → *Chart Do's and Don'ts* and the terminal § Do's and Don'ts). Defensible at this file's scale; a reader looking for a rule must check both. *Fix (optional):* cross-reference each from the other's header.

**N8** — NFR-3's browser list (Chrome / Firefox / Safari / Edge) appears in neither spine. Low impact, but it is a stated constraint with no home. *Fix:* one line in § Foundation.

**N9** — `Add visualization`: nothing says whether the same optional plot can be added twice, or whether already-added items become disabled/checked in the `Menu`. *Fix:* add one clause to the *`Add visualization` control* row — proposed: added items render as checked-and-disabled in the menu.

**N10** — § State Patterns → *Comparison at cap* specifies the disabled-with-reason treatment for the promoted-3 chip row; it does not say whether the same treatment applies inside the `Show all methods` expander. *Fix:* state that the cap rule applies to every chip on the surface, and reaffirm that an incompatibility reason always wins over a cap reason (already stated for the promoted row).

---

## Mechanical notes

- **Frontmatter:** DESIGN.md — 162 key paths, well-formed, kebab-case throughout, hex values quoted. Missing `sources` (S6). EXPERIENCE.md — well-formed; `sources` present and all four paths resolve on disk.
- **Cross-file naming:** component names are identical across DESIGN.md § Components, DESIGN.md `components` frontmatter, and EXPERIENCE.md § Component Patterns — with the single exception of *Comparison table*, which names two different objects (B2).
- **Glossary consistency:** persona names (Learner / Practitioner / Explorer / Instructor) are verbatim from the PRD; method names, FR identifiers, and band thresholds match the PRD exactly. Timeout tiers match FR-8.4 and correctly document the memlog-locked override of NFR-1.
- **`[ASSUMPTION]` tags:** 27 in EXPERIENCE.md, 9 in DESIGN.md. Per instruction, not treated as defects. Checked against the memlog: **none contradicts a locked decision**, and none is unreasonable. Two are worth the author's attention on their merits rather than their form — the `textTransform: 'none'` button override (DESIGN.md § Typography, self-identified as a taste call) and the green-up delta framing (DESIGN.md § Colors, which the author's own counter-metrics may argue against; the file already proposes the alternative).
- **Visual references:** `imports/` empty; no `mockups/` or `wireframes/`. No orphans, no unspecific links, and no spines-win-on-conflict statement is needed.
- **Tables:** all render; no broken pipes. No Mermaid in either file.
