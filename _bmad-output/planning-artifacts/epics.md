---
stepsCompleted: ["step-01-validate-prerequisites"]
inputDocuments:
  - _bmad-output/planning-artifacts/prds/prd-TFM-2026-07-26/prd.md
  - _bmad-output/planning-artifacts/prds/prd-TFM-2026-07-26/addendum.md
  - _bmad-output/planning-artifacts/ux-designs/ux-TFM-2026-08-08/DESIGN.md
  - _bmad-output/planning-artifacts/ux-designs/ux-TFM-2026-08-08/EXPERIENCE.md
architectureDocument: NONE — epics written tech-agnostic by author decision (2026-08-08)
---

# TFM - Epic Breakdown

## Overview

This document provides the complete epic and story breakdown for the TFM explainable supervised-learning method recommender, decomposing requirements from the PRD and the UX design contract (DESIGN.md + EXPERIENCE.md) into implementable stories.

> **No Architecture document exists.** The author elected to write epics tech-agnostic and settle the stack (frontend framework, backend framework, chart rendering library) in a later architecture phase. Stories therefore describe **behavior and outcome**, never implementation technology. Any story whose acceptance criteria would depend on the stack carries an explicit `[STACK-DEPENDENT]` marker for revisit after architecture lands.

## Requirements Inventory

### Functional Requirements

**FR-1 Problem Characterization Form**
- FR-1.1: The form adapts based on whether the user uploads a dataset.
- FR-1.2: On upload, the user selects the target column from a dropdown of all column names; the system auto-detects prediction type, row count, feature count, feature types, missing-value rate, and class balance, and asks the user to confirm.
- FR-1.3: With no dataset, the user answers manually using banded options (rows, features, feature types, missing values, class balance, prediction type).
- FR-1.4: Always asked regardless of upload: explainability importance, non-linearity suspicion, feature interactions.
- FR-1.5: On opt-in, the system reads column names to suggest likely feature interactions.
- FR-1.6: Every question carries an inline educational explanation; no prior ML knowledge required.
- FR-1.7: The dashboard updates only on "Get Recommendation" — never on form change.

**FR-2 Recommendation Engine**
- FR-2.1: Hybrid engine — rule-based heuristics plus a benchmark-trained model.
- FR-2.2: Outputs the recommended method with fit score, 3 ranked alternatives, bias-variance position, interpretability note, key decision factors, a method-selection flowchart, and a method characteristics table.
- FR-2.3: Explanations are tool-agnostic — plain language, no textbook or paper references.
- FR-2.4: No feedback modal in v1; satisfaction is measured behaviorally (see Measurement Behavior).

**FR-3 EDA Visualization**
- FR-3.1: EDA appears only when a dataset is uploaded.
- FR-3.2: The EDA section is collapsible, collapsed by default.
- FR-3.3: EDA includes per-feature distributions, correlation heatmap, outlier boxplots, target distribution, and categorical bar charts.

**FR-4 Model Results Visualization**
- FR-4.1: Model results appear after "Get Recommendation" and training completion.
- FR-4.2: Each method has a fixed visualization set.
- FR-4.3: 2-D projections auto-select the 2 most important features; the user can swap them.
- FR-4.4: "Add visualization" offers additions from a closed library.

**FR-5 Interactive Comparison Mode**
- FR-5.1: Up to 3 alternatives may be compared (4 total including the recommendation).
- FR-5.2: "Run comparison" triggers it; the recommended method is the reference column.
- FR-5.3: Side-by-side view with CV score (mean ± SD), accuracy/RMSE, and method-specific plots.
- FR-5.4: A ranking of compared methods by CV score with delta % vs the reference; ties within 1 SD shown as tied.
- FR-5.5: A feedback prompt below the ranking: did results match expectations, plus which method the user would use, plus optional free text.

**FR-6 Benchmark Transparency Page**
- FR-6.1: A dedicated Benchmark page exposes the data behind the recommender.
- FR-6.2: Shows a dataset × method performance heatmap, a heuristic-vs-empirical agreement indicator, and per-row error reporting.
- FR-6.3: Dataset provenance is visible (OpenML-CC18 for classification, UCI for regression).
- FR-6.4: The benchmark evaluation is a formal secondary research objective, including Random (lower bound) and AMLBID (upper bound) baselines. **In scope as Epic 1** — it produces the trained model FR-2.1's Layer 2 depends on, so it is a prerequisite, not an offline appendix.

**FR-7 Backend & Data Policy**
- FR-7.1: A backend handles in-memory dataset processing, training and inference, benchmark model serving, and anonymized session storage.
- FR-7.2: User datasets are processed in memory only — never written to disk or persistent storage.
- FR-7.3: The backend permanently stores an anonymized per-session record: decision drivers, the recommendation, methods run (with origin flag), and feedback.
- FR-7.4: A privacy notice states that datasets are never stored and anonymized decision data is collected.

**FR-8 Error Handling & Training Control**
- FR-8.1: Invalid CSV is rejected immediately with a clear message.
- FR-8.2: Low-confidence auto-detection is flagged for manual confirmation, never silently accepted.
- FR-8.3: Methods incompatible with the task type appear **disabled with the reason stated** — never hidden.
- FR-8.4: Up to 5 methods trained in fit-score order, sequentially; early halt when the top 3 fall within 1 SD; per-method timeout tiered by dataset size (60s / 120s / 300s); timeout affects only that method and completed results still display.
- FR-8.5: Files over 50MB or 500 features are rejected with a specific message.

### NonFunctional Requirements

- **NFR-1 Performance**: recommendation without dataset under 5s; training shows a loading indicator with an honest estimate; per-method timeout per FR-8.4; max upload 50MB.
- **NFR-2 Dataset Constraints**: CSV only; max 500 features; numeric and categorical only (no image, text, or datetime columns in v1).
- **NFR-3 Browser Support**: modern browsers only (Chrome, Firefox, Safari, Edge). Desktop-first; no mobile optimization in v1.
- **NFR-4 Security & Privacy**: no authentication; no SLA; datasets never persisted; only anonymized decision records and feedback stored.

### Additional Requirements

> **Settled 2026-08-16 (D-013, D-014).** The stack questions below are closed. What remains open is noted inline.

- **[DECIDED] Frontend — React + MUI.** Streamlit was roughly half the hours but cannot express the interaction model in `EXPERIENCE.md`; the UX contract was chosen instead (D-014).
- **[DECIDED] Backend — FastAPI.**
- **[DECIDED] Chart rendering — client-side.** This keeps the per-panel toggles, tooltips and interaction rules in `EXPERIENCE.md` valid. **v1 ships two chart types, not four** (D-014).
- **[DECIDED] Deployment — HuggingFace Spaces**, single container. Deployment was never in the 120h budget of D-011; free Python hosting closes that gap.
- **[DECIDED] Benchmark study language — Python-first**, with a narrow optional R step for BART (D-001). Fold assignments are generated once and persisted so any participating language evaluates on identical splits.
- **[DECIDED] Data source — PMLB**, superseding OpenML's CC18 and CTR23 after a documented, recurring API outage. CC18 returns as optional validation if the API recovers (D-013).
- **[OPEN] Session storage** for form-answer restore and the stale-input snapshot.
- **[OPEN] Anonymized record store** for FR-7.3 — deferred with the measurement instrumentation under D-011.
- No starter template is specified.

### UX Design Requirements

Extracted from the DESIGN.md + EXPERIENCE.md spine pair. These are first-class implementation requirements, not styling suggestions.

**Design tokens and visual foundation**
- UX-DR1: Implement the MUI light theme at near-stock defaults — primary `#1976d2`, Roboto ramp, 4px radius, 8px spacing base — with only the documented overrides.
- UX-DR2: Implement the validated categorical chart palette as fixed slots: series-1 `#2a78d6` (permanently the recommended method), series-2 `#eb6834`, series-3 `#1baf7a`, series-4 `#eda100`, series-other `#757575`.
- UX-DR3: Implement the sequential blue ramp (8 steps) for magnitude encodings and the blue↔red diverging ramp (9 steps) for correlation and signed values.
- UX-DR4: Implement reserved status colors that are never used as a chart series.
- UX-DR5: Implement the chart-specific typography scale (chart title, subtitle, axis label, tick, legend, annotation) with an 11px floor.
- UX-DR6: Implement delta rendering as **neutral ink with ▲/▼/= glyphs** — no green/red — per the measurement-bias decision.

**Reusable components (17 specified)**
- UX-DR7: `app-bar` — non-sticky, elevation 0 with bottom divider, title-as-home-link, single Benchmark link.
- UX-DR8: `form-summary-bar` — the single sticky element; collapsed one-line summary with Edit.
- UX-DR9: `plot-panel` — fixed aspect box, per-panel View as table / View as text toggle, height-stable across modes.
- UX-DR10: `fit-score-meter` — 40px numeral plus single-hue meter, not threshold-colored.
- UX-DR11: `method-chip` and `method-chip-disabled` — the latter carrying `aria-disabled` + `tabindex` + `aria-describedby` and an always-legible reason.
- UX-DR12: `stale-results` — dim plus desaturate with a non-dimmed sticky info banner; non-destructive.
- UX-DR13: `shared-metrics-row` — the only aligned object in comparison mode; never wraps; becomes a stacked table below the single-column breakpoint.
- UX-DR14: `method-characteristics-table` — qualitative, always present including advice-only mode; word-primary cells with a redundant ordinal dot count; no series or status color.
- UX-DR15: `comparison-results` — the empirical ranking table with tie handling and em-dash reference cell.
- UX-DR16: `decision-flowchart` — rendered graph with a four-channel traversed-path encoding; collapses to a vertical step list at narrow widths.
- UX-DR17: `benchmark-heatmap` — sticky row/column headers, 24px cell minimum, virtualization above 100 rows, mandatory legend, persistent per-row Report an error button.
- UX-DR18: `correlation-heatmap` — hard cap at the 30 highest-variance features with a visible disclosure line.
- UX-DR19: `tree-diagram` — depth cap 4 with a truncation node and a subtitle stating the truncation.
- UX-DR20: `delta-badge-*` variants for better / worse / tied.

**Chart system**
- UX-DR21: Implement the ~29 chart forms across 10 plot families with their fixed per-method mapping.
- UX-DR22: Enforce the series-slot register: slot 1 permanently the recommended method; new selections take the lowest free slot; already-rendered methods never repaint.
- UX-DR23: Enforce the series caps — 4 series on overlaid lines/bars, 3 on scatter, decision boundaries, pairwise scatter, and small multiples.
- UX-DR24: Implement the multiclass banding: ≤3 classes one frame, 4–6 facet one-vs-rest, >6 the boundary plot is not rendered and the user is told why.
- UX-DR25: Implement scale guards with visible disclosure — coefficients top 20, categorical bars top 15, confusion-matrix annotation ≤10 classes, facet cap 6.

**States**
- UX-DR26: Implement the full state set — initial/empty, advice-only, detection in flight, low-confidence detection, loading with honest tiered estimate and Stop training, per-method timeout with partial results, early halt with disclosure, stale, comparison running, tie, benchmark load failure and empty, and the degenerate-dataset cases.
- UX-DR27: Implement re-run cache invalidation keyed on a canonicalized input snapshot, invalidated at change time.

**Accessibility**
- UX-DR28: Color is never the sole carrier of meaning in any chart — direct labels, glyphs, dash patterns, and marker shapes carry it redundantly.
- UX-DR29: Every chart family has a non-visual equivalent — a table for most, a specified text summary for decision boundary, tree diagram, and method-selection flowchart.
- UX-DR30: Keyboard access throughout, including a roving-tabindex 2-D grid for the benchmark heatmap and a skip link ahead of the top bar.
- UX-DR31: Honor the 13-row load-bearing accessibility register — cutting any listed specification requires deleting the matching claim from the spec and the thesis.

**Responsive**
- UX-DR32: Implement the breakpoint ladder — 4 comparison columns at ≥1416px, 3 at 1100–1415px, 2 at 800–1099px, single column below 800px — never violating the 320px panel minimum, with in-panel horizontal scroll as the only scroll.

**Education layer**
- UX-DR33: Author and integrate the full explanation string catalogue — inline explanations for all form questions in both form shapes, chart subtitles, disabled reasons, and state messages — plain language, citation-free, following the written copy specimens.

### FR Coverage Map

| FR | Epic | Note |
|---|---|---|
| FR-1.1, 1.3, 1.4, 1.6, 1.7 | Epic 2 | Form, manual branch, always-asked questions, inline education, button-triggered |
| FR-1.2, 1.5 | Epic 3 | Upload-dependent: target selection, auto-detection, column-name interactions |
| FR-2.1 | Epic 1 + Epic 2 | Layer 2 model trained in Epic 1; Layer 1 heuristics and the blend in Epic 2 |
| FR-2.2, 2.3 | Epic 2 | Recommendation output, flowchart, characteristics table, citation-free copy |
| FR-2.4 | Epic 2 | Behavioral measurement — record schema and origin flags established here |
| FR-3 | Epic 3 | EDA layer |
| FR-4 | Epic 4 | Model results and per-method visualizations |
| FR-5 | Epic 5 | Comparison mode, ranking, feedback prompt |
| FR-6.1, 6.2, 6.3 | Epic 6 | Benchmark page, heatmap, provenance, error reporting |
| FR-6.4 | Epic 1 | Benchmark study, baselines, and research metrics |
| FR-7.1, 7.3 | Epic 2 | Backend and session-record storage established; later epics extend the record |
| FR-7.2 | Epic 3 | In-memory-only processing becomes real once datasets exist |
| FR-7.4 | Epic 2 | Privacy notice |
| FR-8.1, 8.2, 8.5 | Epic 3 | Upload and detection error handling |
| FR-8.3 | Epic 5 | Disabled-with-reason surfaces in the comparison selector |
| FR-8.4 | Epic 4 | Training control, early halt, tiered timeouts |

All NFRs are cross-cutting and are enforced within the epic that first makes them observable: NFR-1 in Epics 2 and 4, NFR-2 in Epic 3, NFR-3 and NFR-4 throughout.

## Epic List

### Epic 1: Establish the evidence base

Run the benchmark study that both grounds the recommender and constitutes the thesis's secondary research contribution. Curate datasets, evaluate every candidate method under cross-validation, and train the Layer 2 model the recommendation engine depends on.

**Why first:** FR-2.1 specifies a hybrid engine — heuristics plus a benchmark-trained model. Without this epic there is no Layer 2, and the research metrics that justify the whole approach have nothing to report.

**FRs covered:** FR-6.4, FR-2.1 (Layer 2 only), FR-6.3 (provenance captured at curation time)

**Delivers:** a reproducible benchmark pipeline, a per-dataset method ranking, a trained recommender model, Random and AMLBID baselines, and the three research metrics (top-1 hit rate, regret, Spearman rank correlation).

---

### Epic 2: Get a recommendation without uploading anything

A person describes their problem in a form and receives a justified method recommendation with a plain-language explanation — no dataset required. This is the complete advice-only product and ships as a useful tool on its own.

**FRs covered:** FR-1.1, FR-1.3, FR-1.4, FR-1.6, FR-1.7, FR-2.1, FR-2.2, FR-2.3, FR-2.4, FR-7.1, FR-7.3, FR-7.4

**Also owns:** the anonymized session-record schema and the run-origin flag mechanism that every later epic writes to — designed once here so measurement integrity cannot be quietly lost.

---

### Epic 3: Upload your dataset and understand it

A person uploads a CSV, confirms what the system detected about it, and explores it visually before any model is trained.

**FRs covered:** FR-1.2, FR-1.5, FR-3, FR-7.2, FR-8.1, FR-8.2, FR-8.5

---

### Epic 4: Watch the recommended method actually run

The recommended method is trained on the person's own data and its results are shown with the visualizations that make that method's behavior legible.

**FRs covered:** FR-4, FR-8.4

---

### Epic 5: Challenge the recommendation

A person selects alternative methods, runs them against their own data, and sees whether the recommendation actually held up.

**FRs covered:** FR-5, FR-8.3

---

### Epic 6: See the evidence behind the recommender

A person inspects the benchmark data the recommender is built on, judges it for themselves, and reports errors in it.

**FRs covered:** FR-6.1, FR-6.2, FR-6.3

**Depends only on Epic 1** — buildable at any point after the benchmark exists.

---

### Cross-cutting decisions

- **No "backend" or "design system" epic.** Both would be technical layers with no standalone user value. The record schema is established in Epic 2; design tokens and shared components are built by the first epic that needs them.
- **Accessibility is not a separate epic.** The 13-row load-bearing accessibility register (UX-DR31) is distributed across the epics that own each surface, because deferring accessibility to a final epic is reliably how it gets dropped.
- **Every epic after Epic 1 is `[STACK-DEPENDENT]`** until the architecture phase settles the frontend, backend, and chart-rendering decisions. Epic 1 is the exception: it is an offline research pipeline and can start immediately.
