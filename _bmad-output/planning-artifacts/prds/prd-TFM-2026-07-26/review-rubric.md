# PRD Quality Review — TFM Explainable Supervised Learning Recommender

**Reviewed:** 2026-07-26
**Verdict:** PASS-WITH-ISSUES

---

## Critical Issues

### CRITICAL-1: No acceptance criteria for the hybrid recommendation engine (FR-2.1)

FR-2.1 describes a two-layer engine (rule-based + benchmark-trained model) but provides zero implementation-testable criteria for either layer. Specifically:

- The rule-based layer is described as "ISLR theory encoded as decision rules" — there is no specification of which rules, in what priority order, or what outputs they map to. This is unimplementable without a separate rules document that does not exist in the PRD or addendum.
- The benchmark-trained model layer has no specified model type, training target, feature space (what meta-features go in?), or prediction output format. The PRD says it "refines or overrides Layer 1 when empirical evidence disagrees" but gives no threshold or logic for when override occurs.
- FR-2.2 specifies a "fit score" for the primary recommendation but does not define the scoring range, what it measures (is it the benchmark CV score? a composite of rule strength + empirical score?), or how it is computed.

**Risk:** Two engineers implementing this independently would produce incompatible systems. The recommendation engine is the core differentiator of the product and is essentially unspecified at the implementation level.

**Fix required:** Add an FR-2.x sub-requirement that names: (a) the concrete rule set or points to a rules appendix, (b) the meta-features used as input to Layer 2, (c) the model type or selection rationale for Layer 2, (d) the override logic, and (e) how the fit score is computed and what its range means.

---

### CRITICAL-2: User satisfaction metrics are unmeasurable given the described system

The Success Metrics section lists:

- "% of users rating the recommendation as useful (FR-2.4 feedback)"
- "% of users agreeing the winner call matched their expectations (FR-5.5 feedback)"

FR-2.4 states the feedback prompt is **low priority within v1 — implemented after core features are complete.** FR-5.5 feedback is similarly optional free-text. There is no requirement that these responses are ever stored or aggregated — the backend (FR-7.3) stores feedback as a field in the session record, but there is no requirement for an admin view, export mechanism, or query interface to retrieve aggregate statistics.

The satisfaction metrics as written cannot be measured without:
1. A guaranteed implementation of FR-2.4 (not "low priority, maybe later")
2. A defined response format (binary yes/no is measurable; free-text is not directly)
3. A data access mechanism to compute the percentage

**Risk:** These metrics will be listed in the thesis but will be impossible to report on at submission time if FR-2.4 remains deprioritized.

**Fix required:** Either (a) elevate FR-2.4 to required and specify a binary response format, or (b) remove the satisfaction metrics from the Success Metrics section and replace them with metrics derivable from the stored data that is guaranteed to exist (e.g., "% of sessions where user ran at least one comparison" derived from FR-7.3 `methods_run_by_user`).

---

## High-Severity Issues

### HIGH-1: Contradiction between FR-5.1 and FR-5.4 on what constitutes the "winner"

FR-5.1: "the user can select up to 3 alternative methods to compare (4 total including the recommended method)."
FR-5.4: winner call says "[method X] outperformed the recommended [method Y]" — implying X is one of the 3 alternatives.

But there is no requirement specifying the winning criterion. Is the winner the method with the highest mean CV score? Highest accuracy on a held-out split? Highest RMSE improvement for regression? The comparison view (FR-5.3) shows "CV score (mean ± std), accuracy/RMSE" — these can conflict (a method may have higher mean CV but worse accuracy on the test split). The winner call needs a tie-breaking rule and a primary metric definition.

Additionally, the winner call states a delta percentage — but percentage of what? CV score? Accuracy? This needs to be specified or the frontend cannot render the message.

**Fix required:** Add FR-5.x specifying the winning metric (recommend: mean CV score as primary, with task-appropriate secondary metric), tie-breaking rule, and the definition of the delta reported in the winner call.

---

### HIGH-2: Missing error handling for all interactive flows

The PRD contains zero error-handling requirements across FR-1 through FR-7. The following failure modes are implied but unaddressed:

- **FR-1.2**: What happens if the uploaded CSV has no valid numeric or categorical columns? What if the user-selected target column has all-unique values (no valid classification target)?
- **FR-2**: What does the UI show if the recommendation engine fails or produces no valid recommendation for the given inputs?
- **FR-4 / FR-5**: What if model training fails (e.g., singular matrix in LDA, BART exceeds memory)? FR-7 specifies a 60-second timeout per method — what does the UI show when a timeout fires? Is the session record still stored?
- **FR-5**: What happens if the user selects a method incompatible with the detected task type (e.g., selects a classification method for a regression task)?
- **FR-7.2**: Dataset processed in memory only — what if the server runs out of memory for a 50MB file with 500 features?

**Fix required:** Add a single FR-7.x or NFR requirement enumerating the minimum error states the system must handle gracefully, with "graceful" defined as: user sees an actionable message (not a stack trace), the session record is marked with the failure reason, and the user can retry without reloading the page.

---

### HIGH-3: FR-4.4 "Add visualization" is too vague to implement

FR-4.4 states: "The user can add extra visualizations beyond the fixed set via an 'Add visualization' control."

This requirement is unimplementable as written. It specifies neither:
- What the universe of additional visualizations is (any chart? only from a fixed extension menu? user-configurable chart builder?)
- Whether these additional visualizations are per-method or global
- Whether they are stored/restored in the comparison view
- Whether they affect the recommendation or are purely exploratory

This is the kind of open-ended feature that can explode scope or become a dead UI element that does nothing useful.

**Fix required:** Either (a) enumerate the available additional visualization types per method group (e.g., "for tree methods: partial dependence plot, SHAP summary plot"), or (b) explicitly descope FR-4.4 to v2 and remove it from v1 requirements.

---

## Notes (not blocking)

- **Open Question: benchmark re-run cadence** — this is not just a nice-to-have architectural question. If the benchmark is fixed at thesis submission time, the Layer 2 model is static and there is no data freshness concern. If it is periodic, FR-7.1 needs a background job requirement. The PRD should close this before architecture begins.
- **NFR-1 timeout (60s per method)** — BART is a Bayesian method that can be extremely slow. 60 seconds may be insufficient for BART on a 50MB dataset with 500 features even on capable hardware. Consider either excluding BART from the training flow (recommendation only, no visualization) or specifying a separate timeout for Bayesian methods.
- **FR-6.2 "Report an error" button** — where does this report go? There is no requirement for what happens on submit, where errors are routed, or whether they affect the benchmark data. If this is out-of-scope boilerplate, remove it. If it is in scope, add a handling requirement.

---

## Summary Table

| ID | Severity | Area | One-line summary |
|---|---|---|---|
| CRITICAL-1 | Critical | FR-2.1 | Recommendation engine unspecified — no rules, no meta-features, no fit score definition |
| CRITICAL-2 | Critical | Success Metrics | Satisfaction metrics unmeasurable if FR-2.4 remains low-priority |
| HIGH-1 | High | FR-5.4 | Winner call has no defined winning metric or delta definition |
| HIGH-2 | High | FR-1/4/5/7 | Zero error-handling requirements across all interactive flows |
| HIGH-3 | High | FR-4.4 | "Add visualization" unimplementably vague — scope unclear |
