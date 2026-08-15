# Reconciliation: propuesta-tfm.md vs PRD

## Gaps Found

### 1. Bias-Variance Tradeoff as Explicit Explanation Layer
The source specifies that recommendations must be justified using the **bias-variance tradeoff** as a named conceptual anchor, alongside the ISLR comparative table and a model-selection flowchart. The PRD describes a hybrid recommendation engine and EDA/result visualizations but does not call out the bias-variance tradeoff or the ISLR method-comparison table as required explanation artifacts. These are didactic framing devices central to the source's educational mission.

### 2. Empirical Validation as a Formal Secondary Objective
The source frames the benchmark evaluation as a **secondary research objective**: to empirically test whether the recommender's didactic heuristics hold up against real method performance. This is a distinct research question with its own methodology (benchmark dataset selection, cross-validation of all candidate methods, comparison against random-selection lower bound and AMLBID upper bound). The PRD's benchmark transparency page (FR-6) covers surfacing benchmark data but does not articulate this as a formal research hypothesis or secondary deliverable.

### 3. AMLBID as an Explicit Comparison Baseline
The source names **AMLBID** as the upper-bound baseline for evaluating the recommender's accuracy. The PRD does not mention AMLBID anywhere — neither as a referenced system, a benchmark comparison baseline, nor a literature anchor. This is a concrete methodological constraint that affects how evaluation results are interpreted.

### 4. Specific Evaluation Metrics: Regret and Spearman Correlation
The source defines three concrete evaluation metrics: **Top-1 hit rate**, **Regret**, and **Spearman rank correlation**. The PRD lists success metrics (research + satisfaction + quality + counter-metrics) but does not specify these three metrics by name. Regret and Spearman correlation are non-obvious choices that encode specific assumptions about what "good recommendation" means and should be captured explicitly.
