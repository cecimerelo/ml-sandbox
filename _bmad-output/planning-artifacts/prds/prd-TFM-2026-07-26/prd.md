---
title: TFM — Explainable Supervised Learning Method Recommender
status: final
created: 2026-07-26
updated: 2026-07-26
---

## Vision

TFM is an interactive web tool born from the author's own master's learning journey — the recurring difficulty of knowing which supervised learning method actually fits a given problem. It helps anyone curious about machine learning navigate that same question: the user describes their dataset and goals through a guided form, uploads their data, and receives a theory-grounded recommendation — explained using concepts like the bias-variance tradeoff and the interpretability-flexibility spectrum — along with EDA visualizations and the option to train, visualize, and compare alternative methods side by side.

## Problem Statement

Existing tools fall into two camps: interactive playgrounds (TensorFlow Playground, Decision Boundary Playground) that build visual intuition but only work on synthetic data; and AutoML/meta-learning systems (Auto-WEKA, AMLBID) that work on real data but produce black-box recommendations with no pedagogical justification. No tool combines real user data, theory-grounded explanation, and interactive comparison in a single experience.

## Target Users

| User | Goal |
|---|---|
| **Learner** | Understand which supervised method fits their problem, backed by theory — they know methods exist but can't map them to a real dataset decision |
| **Practitioner** | Quick method sanity-check with visual evidence for a real prediction problem |
| **Explorer** | Curiosity-driven — upload a dataset, run several methods, see what happens |
| **Instructor** | Demonstrate methods and tradeoffs to students in a classroom setting |

No prior ML knowledge is assumed. The form educates as it asks — every question includes an inline explanation.

## Methods in Scope (v1 — Supervised Learning Only)

| Area | Methods |
|---|---|
| Linear Regression | Simple LR, Multiple LR, KNN Regression |
| Classification | Logistic Regression, LDA, QDA, Naive Bayes, KNN |
| Regularization | Ridge, Lasso, PCR, PLS |
| Non-linear | Polynomial Regression, Splines, GAMs |
| Tree-based | Decision Trees, Bagging, Random Forests, Boosting, BART |
| SVM | Support Vector Classifier, SVM (kernel) |
| Deep Learning | MLP Neural Networks |

Unsupervised methods (PCA, K-Means, Hierarchical Clustering) are deferred to v2.

## Features

### FR-1 Problem Characterization Form

**FR-1.1** The form adapts based on whether the user uploads a dataset.

**FR-1.2** When a dataset is uploaded, the user selects the target column from a dropdown listing all column names. The system then auto-detects and displays for user confirmation:
- Prediction type (regression / binary classification / multiclass — inferred from target column value types)
- Row count
- Feature count
- Feature types (numeric / categorical / mixed)
- Missing value rate
- Class balance *(classification only)*

**FR-1.3** When no dataset is uploaded, the user answers manually:
- Prediction type *(regression / binary classification / multiclass)*
- Row count *(< 500 / 500–10k / > 10k)*
- Feature count *(< 10 / 10–50 / > 50)*
- Feature types *(numeric / categorical / mixed)*
- Missing values *(none / some / a lot)*
- Class balance *(classification only — roughly equal / one class dominates)*

**FR-1.4** The following questions are always asked, regardless of dataset upload:
- Explainability importance *(not important / somewhat / critical)*
- Non-linearity suspicion *(no / unsure / yes)*
- Feature interactions *(do you think any features interact with each other?)*

**FR-1.5** When a dataset is uploaded and the user opts in, the system reads column names to suggest likely feature interactions (e.g. "we noticed `age` and `income` — do these interact?"). The user confirms or adjusts. This is opt-in via a toggle ("Use column names to improve suggestions", default on).

**FR-1.6** Every question includes an inline educational explanation so no prior ML knowledge is required to answer.

**FR-1.7** The dashboard updates only when the user clicks "Get Recommendation" — not on every form change.

---

### FR-2 Recommendation Engine

**FR-2.1** The engine uses a hybrid approach:
- **Layer 1 — Rule-based heuristics**: ISLR theory encoded as decision rules; always produces a result, fast, interpretable.
- **Layer 2 — Benchmark-trained model**: trained on cross-validation results from the benchmark dataset collection; it refines or overrides Layer 1 when empirical evidence disagrees.

The engine reads the user's form answers as its inputs — prediction type, dataset size, feature count, feature types, missing value rate, class balance, explainability need, non-linearity suspicion, and feature interactions. For each candidate method it produces a score from 0 to 1 indicating how well that method fits the user's problem. The method with the highest score becomes the primary recommendation.

**FR-2.2** The engine outputs:
- **Primary recommendation** — one method with a fit score
- **Ranked alternatives** — the next 3 methods ordered by suitability
- **Explanation** including:
  - Bias-variance position: where the recommended method sits on the bias-variance spectrum (high bias / balanced / high variance) given the user's data size and complexity
  - Interpretability note: how explainable this method is relative to what the user asked for, on the interpretability-flexibility spectrum
  - Key decision factors: which form answers drove the recommendation (e.g. "small dataset + interpretability critical → Logistic Regression preferred over Random Forest")
  - Method selection flowchart: a visual decision path showing how the user's inputs lead to the recommendation
  - Comparison table: recommended method vs. top alternatives across accuracy potential, interpretability, training speed, handles non-linearity, handles missing values

**FR-2.3** Explanations are tool-agnostic — concepts are explained in plain language without referencing any specific textbook or paper.

**FR-2.4** Feedback modal (user rates the recommendation) is deferred to v2. In v1, user satisfaction is measured behaviorally: whether the user ran the recommended method is recorded automatically from stored session data.

---

### FR-3 EDA Visualization

**FR-3.1** EDA is shown only when a dataset is uploaded.

**FR-3.2** The EDA section is collapsible/expandable on the dashboard, collapsed by default.

**FR-3.3** EDA includes:
- Distribution plots per feature (histogram for numeric, bar chart for categorical)
- Correlation heatmap between features
- Outlier detection (boxplots)
- Target variable distribution

---

### FR-4 Model Results Visualization

**FR-4.1** Model results are shown after "Get Recommendation" is clicked and training completes.

**FR-4.2** Each method has a fixed set of visualizations:

| Method | Visualizations |
|---|---|
| Linear Regression | Residual plot, predicted vs. actual scatter, coefficient plot |
| Logistic Regression | ROC curve, confusion matrix, coefficient plot |
| LDA / QDA | Decision boundary, confusion matrix |
| Naive Bayes | Confusion matrix, ROC curve |
| KNN | Decision boundary, accuracy vs. K curve |
| Ridge / Lasso | Coefficient shrinkage path, CV error vs. lambda |
| PCR / PLS | Variance explained vs. components |
| Polynomial Regression / Splines | Fitted curve plot, residual plot |
| GAMs | Partial dependence plot per feature |
| Decision Tree | Tree diagram, feature importance |
| Random Forest / Bagging | Feature importance, OOB error curve |
| Boosting | Feature importance, training vs. test error by iteration |
| BART | Posterior credible intervals, variable inclusion proportions |
| SVM / SVC | Decision boundary *(2D only)*, support vectors highlighted |
| MLP Neural Network | Training vs. validation loss curve, confusion matrix / residual plot |

**FR-4.3** For visualizations requiring 2D projection (decision boundaries), the system auto-selects the 2 most important features. The user can swap the selected features.

**FR-4.4** The user can add extra visualizations beyond the fixed set via an "Add visualization" control. The available additions are drawn from a predefined library: learning curve (train vs. validation score by training size), calibration curve (classification only), feature distributions by class (classification only), and pairwise feature scatter coloured by target. Additional plots are method-agnostic and available for any method.

---

### FR-5 Interactive Comparison Mode

**FR-5.1** After a recommendation is shown, the user can select up to 3 alternative methods to compare (4 total including the recommended method).

**FR-5.2** The user triggers comparison via a "Run comparison" button. The recommended method is the reference column.

**FR-5.3** The comparison view shows each method side by side with: CV score (mean ± std), accuracy/RMSE, and its method-specific plots.

**FR-5.4** After comparison, the system displays a ranking of all compared methods ordered by CV score (mean across folds), showing the delta % relative to the recommended method for each. When two methods are within 1 standard deviation of each other their scores are shown as tied.

**FR-5.5** Below the ranking, the user is shown a feedback prompt: "Did the results match your expectations?" with optional free-text comment. Response is stored in the backend linked to the session's decision drivers record.

---

### FR-6 Benchmark Transparency Page

**FR-6.1** A dedicated "Benchmark" page exposes the data behind the recommender.

**FR-6.2** The page shows:
- A heatmap of dataset × method → performance score across the benchmark collection
- Where the heuristic recommendation agreed or disagreed with empirical results
- An "Report an error" button per method/dataset row

**FR-6.3** Benchmark dataset sources:
- **OpenML-CC18** — 72 curated classification datasets (primary benchmark for classification methods)
- **UCI repository** — regression datasets (supplementary benchmark for regression methods)

**FR-6.4** The benchmark evaluation serves as a formal secondary research objective: empirically testing whether the theory-based heuristics hold up against real method performance. The evaluation compares the recommender against:
- **Random selection** — lower bound baseline
- **AMLBID** — upper bound baseline (meta-learning system from the literature)

This positions the recommender's accuracy relative to both a naive baseline and a state-of-the-art AutoML system.

---

### FR-7 Backend & Data Policy

**FR-7.1** A backend service handles: dataset processing in memory, ML training and inference, benchmark model serving, and permanent storage of anonymized session records and feedback.

**FR-7.2** User datasets are processed in memory only — they are never written to disk or any persistent storage.

**FR-7.3** The backend permanently stores the following anonymized record per session:
- **Decision drivers**: all form answers and auto-detected metadata (prediction type, row count, feature count, feature types, missing rate, class balance, explainability need, non-linearity suspicion, feature interactions)
- **System recommendation**: the primary method recommended by the engine
- **Methods run by user**: which methods the user actually trained and compared
- **Feedback**: satisfaction ratings and optional comments from FR-2.4 and FR-5.5

User adoption is derived at query time by comparing the system recommendation against the method chosen — not stored as a standalone field.

**FR-7.4** A privacy notice is displayed in the UI informing users that: their dataset is never stored, and anonymized decision information is collected to improve the recommender.

---

### FR-8 Error Handling & Training Control

**FR-8.1** If an uploaded file is not a valid CSV, the system rejects it immediately with a clear message before any processing begins.

**FR-8.2** If auto-detection of prediction type or dataset metadata produces a low-confidence result, the system flags it and asks the user to confirm manually rather than silently proceeding.

**FR-8.3** If a method is incompatible with the selected task type (e.g. a classification-only method selected for a regression problem), the system shows it in the comparison selector as disabled, with the reason stated. Incompatible methods are never hidden — the user learns why the method does not apply rather than silently not seeing it.

**FR-8.4** The system trains up to 5 methods ordered by fit score. Training halts early if the top 3 are within 1 standard deviation of each other in cross-validation score. Per-method training timeout is dataset-size dependent:
- Small (< 500 rows): 60 seconds
- Medium (500–10k rows): 120 seconds
- Large (> 10k rows): 300 seconds

If a method exceeds its timeout, its training is cancelled, a timeout notice is shown for that method only, and results for completed methods are displayed.

**FR-8.5** If the uploaded file exceeds 50MB or 500 features, the system rejects it with a specific message stating the limit exceeded.

---

## Non-Functional Requirements

**NFR-1 Performance**
- Recommendation without dataset: < 5 seconds
- Model training with dataset: displays a loading indicator with an estimated time. Per-method timeout is dataset-size dependent — see FR-8.4 for the authoritative values (60s / 120s / 300s by dataset size).
- Max file upload size: 50MB

**NFR-2 Dataset Constraints**
- File format: CSV only
- Max features: 500
- Supported feature types: numeric and categorical (no image, text, or datetime columns in v1)

**NFR-3 Browser Support**
- Modern browsers: Chrome, Firefox, Safari, Edge
- No mobile optimization required in v1

**NFR-4 Security & Privacy**
- No user authentication required
- Datasets never written to persistent storage (FR-7.2)
- Only anonymized decision drivers and feedback stored (FR-7.3)

## Out of Scope — v1

- Unsupervised learning (PCA, K-Means, Hierarchical Clustering)
- Survival analysis
- Hyperparameter tuning
- Mobile optimization
- User authentication / saved sessions
- Excel, JSON, parquet file formats
- Image, text, datetime feature types
- Deployment/production features (inference latency, batch predictions)

## Future Work — v2 Priority Order

1. **Hyperparameter tuning** *(highest priority)* — sliders per method, cross-validated results
2. Unsupervised learning mode
3. User accounts + saved experiments
4. Semi-supervised learning
5. Formal pedagogical evaluation (rubric, panel user study)

## Success Metrics

### Research Metrics
- **Top-1 hit rate**: % of benchmark datasets where the recommended method is the best-performing (or within 1 std dev of the best)
- **Regret**: mean performance gap between the recommended method and the best method across the benchmark
- **Spearman rank correlation**: between the recommender's method ranking and the real cross-validation ranking per dataset

### User Satisfaction Metrics
- **Recommendation acceptance rate**: % of sessions where the user *deliberately chose* the recommended method — that is, explicitly selected it in comparison mode, or completed the session without overriding it (derived from stored session data — no self-reporting required)

  > **Measurement validity note.** This metric counts **user-initiated method runs only**. FR-8.4 auto-trains the top 5 methods by fit score, which always includes the recommended method; counting auto-trained runs as acceptance would make the metric read 100% in every session regardless of user behaviour, rendering it uninformative. The backend must therefore distinguish system-initiated runs from user-initiated selections, and only the latter count toward this metric.

- **Comparison feedback**: % of users agreeing the comparison results matched their expectations (FR-5.5 — free-text analysis optional)

### Accuracy / Quality Metrics
- % of cases where the recommended method lands in the top-3 on the benchmark
- % of cases where heuristic (Layer 1) and empirical model (Layer 2) agree

### Counter-Metrics
- Recommendation diversity across problem types — the recommender must not converge on a single method regardless of input
- The most complex method must not be systematically over-recommended when simpler methods perform comparably

  > **Measurement validity note.** Where a counter-metric is computed over "methods the user ran", it must use **user-initiated selections only**, for the same reason given under acceptance rate. Note additionally that the comparison selector promotes 3 alternatives and places the remainder behind a "Show all methods" expander; any diversity figure derived from user selections is therefore partly a measurement of that interface default, and must be reported as such rather than as unmediated user preference.

## Open Questions

- [ ] Web stack decision (Frontend: React/Vue/Streamlit? Backend: FastAPI/Flask?) — architecture decision, deferred to architecture doc
- [ ] Should the benchmark be re-run periodically or fixed at thesis submission time?
- [ ] Satisfaction metric thresholds (e.g. "≥ 70% positive") — to be defined once initial feedback data is collected
