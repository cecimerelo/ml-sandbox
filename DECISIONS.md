# Decision log

One entry per decision, with a stable ID so it can be cited from issues, commits, and
the thesis. Append only — entries are not edited. If a decision is reversed, mark it
**superseded** and write a new one.

Every entry answers the same four things: what forced the decision, what was chosen,
what was rejected and why, and what it costs.

---

## D-001 — Study language: Python, with an optional R step for BART

**Date:** 2026-08-15 · **Status:** accepted · **Affects:** [#7](https://github.com/cecimerelo/ml-sandbox/issues/7)

**Context.** The study needs a language. R is ISLR-native and has stronger support for
BART, GAMs, and splines. Python has scikit-learn, the most mature OpenML client, and
AMLBID — the study's upper-bound baseline — is a Python package.

**Decision.** Python-first, reserving an isolated R step for BART alone.

**Rejected.**
- *R-first*: would require a bridge for AMLBID and means working in the author's weaker
  language on a time-boxed project.
- *Julia*: MLJ.jl is respectable, but there is no strong BART implementation, the OpenML
  client is less mature, and AMLBID would need reimplementing. The cost buys nothing the
  thesis can claim credit for.

**Consequences.** BART remains unresolved: either an isolated R step reading the shared
fold assignments, or a documented limitation. The application backend language is still
undecided; if it turns out to be R, the Layer 2 model needs an export path.

---

## D-002 — Benchmark sources: OpenML-CC18 and OpenML-CTR23; UCI dropped

**Date:** 2026-08-16 · **Status:** accepted · **Affects:** [#8](https://github.com/cecimerelo/ml-sandbox/issues/8), PRD FR-6.3

**Context.** The PRD specified CC18 for classification and UCI for regression. UCI has no
uniform API, no strict versioning, and no predefined splits — it would mean curating and
justifying the collection dataset by dataset.

**Decision.** Classification from **OpenML-CC18** (72 tasks). Regression from
**OpenML-CTR23** (suite **353**, 35 tasks). The `OpenML-CTR23` alias fails against the
API; the numeric ID must be used.

**Rejected.**
- *UCI*: manual curation, no splits, heterogeneous provenance.
- *Kaggle*: inconsistent licensing, uncontrolled quality, duplicates without attribution.

**Consequences.** The PRD needs correcting. In exchange, a single protocol and a single
citation cover both halves of the study, and the artisanal UCI curation disappears.

---

## D-003 — Splits: OpenML's, not our own

**Date:** 2026-08-16 · **Status:** accepted · **Affects:** [#8](https://github.com/cecimerelo/ml-sandbox/issues/8), [#10](https://github.com/cecimerelo/ml-sandbox/issues/10)

**Context.** [#10](https://github.com/cecimerelo/ml-sandbox/issues/10) requires that fold
assignments be generated once and read by every method. This was wrongly read as "folds
we invent." The contract demands a **single source of truth**, not authorship.

**Decision.** Use OpenML's splits and persist them in the fold file. Small datasets from
outside the suites, which ship no splits, get folds generated under the same contract.

**Rejected.** *Our own folds throughout*: loses comparability with the published CC18
literature in exchange for a consistency the metrics do not need — all of them are
computed within a dataset and then aggregated, so a raw score from one dataset is never
compared against another's.

**Consequences.** CC18 uses 10 folds, not 5: this **doubles the compute** for the
classification half against the current config. In exchange, results are directly
contrastable with published work on CC18.

---

## D-004 — Exclusions justified by the product's own scope

**Date:** 2026-08-16 · **Status:** accepted · **Affects:** [#8](https://github.com/cecimerelo/ml-sandbox/issues/8)

**Context.** The suites contain datasets outside the application's declared scope:
MNIST (785 columns), Fashion-MNIST (785), and Devnagari-Script (1025) are images
flattened to pixels.

**Decision.** Exclude datasets with **more than 500 columns** and those **derived from
images**, applying NFR-2.

**Consequences.** The selection is justified by constraints already written in the PRD
rather than by criteria invented for this study — the strongest defence against the
suspicion that datasets were chosen to flatter the heuristics. The excluded ones were
also the most expensive to compute.

---

## D-005 — No row ceiling in the benchmark; the ceiling lives in the application

**Date:** 2026-08-16 · **Status:** accepted · **Affects:** [#8](https://github.com/cecimerelo/ml-sandbox/issues/8)

**Decision.** The study imposes no row limit; cost is controlled by the tiered timeouts
in FR-8.4. The application does impose one, for response time.

**Consequences.** The benchmark can cover size regimes the application will not serve
live. This is deliberate: it is worth knowing which method wins on large data even if a
user cannot train it in the browser.

---

## D-006 — Subsampling to cover the sub-500-row band

**Date:** 2026-08-16 · **Status:** accepted · **Affects:** [#8](https://github.com/cecimerelo/ml-sandbox/issues/8), [#12](https://github.com/cecimerelo/ml-sandbox/issues/12)

**Context.** **No dataset in either suite has fewer than 500 rows** (minimums: 500 in
CC18, 517 in CTR23). But FR-1.3 defines a `< 500 rows` band, and that is where the
heuristics claim the most: with little data, flexible methods overfit. Leaving it
uncovered means the recommender asserts something the study cannot support — and it is
the likeliest regime among real users, who arrive with coursework data or a small
experiment.

**Decision.** From each base dataset, generate versions of **100, 250, and 500 rows**,
with **3 subsamples per size** (different seeds).

**Rejected.** *Documenting the limitation instead*: honest, but it weakens precisely the
product's most distinctive recommendation.

**Consequences.** The repetitions stop a lucky draw from producing a winner that is
actually noise. Secondary benefit: varying only *n* while holding domain, noise, and
variables constant measures the shift of the best method toward simpler ones directly —
ISLR's bias-variance claim as a controlled experiment.

Accepted risk: a subsample of a large clean dataset is not the same as data that is
genuinely small, which tends to be noisier because measuring is expensive. Hence D-007.

**Evidence added 2026-08-16.** The gap is not incidental to the collection — CC18
*excludes small datasets by construction*. Its generator
([`openml/benchmark-suites`](https://github.com/openml/benchmark-suites/blob/master/OpenML%20Benchmark%20generator.ipynb))
labels them literally:

```python
data_status.update({k: 'Too small' for k in datalist.index[datalist.NumberOfInstances<500]})
```

So the argument is stronger than an observation about minimums: the band the recommender
most needs to validate is outside the suite *by its authors' own design criterion*, and
must therefore be covered another way.

The same source shows CC18 caps features at 5000, where NFR-2 caps at 500 — the product's
own scope is the stricter filter, which is what D-004 relies on.

---

## D-007 — Real small datasets from general OpenML, as a pinned ID list

**Date:** 2026-08-16 · **Status:** accepted · **Affects:** [#8](https://github.com/cecimerelo/ml-sandbox/issues/8)

**Context.** Subsampling gives experimental control but not external validity. Real small
datasets are added, from outside the suites.

**Decision.** Select from **general OpenML** (not Kaggle, not UCI) and **pin an explicit
list of IDs** in the repository.

**Rejected.** *A dynamic criterion* such as "every dataset with 50–500 rows": the result
would change whenever someone uploads a new dataset, and the study would stop being
reproducible.

**Consequences.** The "curated suite" argument is lost for this portion, and the
selection criteria must be justified. Exploration happens through the web interface,
verification through the API.

Bias to declare in the thesis: the search is sorted by run count, which favours
established, well-formed datasets. The small band may be more benign than it would be
with arbitrary data.

---

## D-008 — Disk cache is mandatory

**Date:** 2026-08-16 · **Status:** accepted · **Affects:** [#8](https://github.com/cecimerelo/ml-sandbox/issues/8), [#10](https://github.com/cecimerelo/ml-sandbox/issues/10)

**Context.** OpenML's v1 listing endpoint returned **repeated 504s**. Queries by ID and
by suite do respond. The web interface works because it uses the newer v2 backend; the
Python client talks to v1.

**Decision.** Every downloaded dataset is cached to disk. A re-run cannot depend on the
server being alive.

**Consequences.** The study stops being reproducible only while the network cooperates,
which is an improvement. The cache is not versioned in git.

---

## D-009 — Acceptance rate measures deliberate choice, not execution

**Date:** 2026-08-08 · **Status:** accepted · **Affects:** PRD (Success Metrics), [#2](https://github.com/cecimerelo/ml-sandbox/issues/2), [#5](https://github.com/cecimerelo/ml-sandbox/issues/5)

**Context.** The PRD measured satisfaction as "% of sessions where the user ran the
recommended method." But FR-8.4 auto-trains the top 5 by fit score, and the recommended
method is by definition first: **it always runs**. The metric would read 100% in every
session regardless of what the user did. It could not fail, so it could not inform.

**Decision.** Only **user-initiated** runs count. Acceptance splits into two arms
reported separately: explicit choice (strong signal) and absence of override (weak
signal).

**Consequences.** The backend must record the origin of every run. Additionally, FR-5.2
makes the recommended method non-deselectable, so "explicitly choosing it" had no way to
be expressed in the interface: the question *which method would you use?* was added to
the FR-5.5 prompt, never pre-filled.

The selector path used is logged as a covariate, because the selector promotes 3
alternatives and hides the rest — any diversity measure partly reflects that default and
must be reported as such.

---

## D-010 — Publish a frozen mirror of the dataset snapshot

**Date:** 2026-08-16 · **Status:** accepted · **Affects:** [#8](https://github.com/cecimerelo/ml-sandbox/issues/8)

**Context.** OpenML's API went down for a full working session during curation, with its
status page reporting normal throughout. That is recoverable — the study only needs
OpenML once, since D-008 caches everything to disk and re-runs are self-contained.

The unrecovered risk is durability. A local cache dies with the laptop, and OpenML can
withdraw or re-version a dataset. Either would leave the thesis citing a collection that
can no longer be assembled.

**Decision.** OpenML remains the **source of record** — the citation, the provenance, the
"curated suite" argument. Separately, publish the **exact snapshot used** as a frozen,
revision-pinned mirror, so the study can be reproduced regardless of OpenML's state.

**Rejected.** *Switching sources to HuggingFace because of the outage.* An outage passes;
a methodological choice stays in the thesis forever. There is also no official OpenML
mirror on HuggingFace — `openml/credit-g` and similar return 401, meaning they do not
exist, while a known public dataset returns 200 from the same unauthenticated endpoint.
`inria-soda/tabular-benchmark` is a genuine curated alternative with a citable paper, but
adopting it would forfeit the predefined splits of D-003 and, by its own construction,
excludes the small datasets that motivated D-006.

**Consequences.** Reproducibility improves beyond the original plan: the thesis moves
from *"download these ids and trust they are unchanged"* to *"here is the exact frozen
collection."*

**Licensing must be checked before publishing.** Datasets carry licences and not all
permit redistribution. The client already records the `licence` field for this reason;
anything that cannot be redistributed is referenced by id rather than mirrored, and the
gap is stated.

---

## D-011 — Scope cut to fit the submission deadline

**Date:** 2026-08-16 · **Status:** accepted · **Affects:** all epics

**Context.** Submission is due before October: roughly six weeks at about 20 hours a
week, or ~120 hours total, and that must also cover writing the thesis. The planned
scope — six epics, ~29 chart types, 17 components, the full benchmark study with two
baselines — does not fit. The supervisor expects both a written thesis and a working
tool.

The failure mode being avoided is not an incomplete application. It is arriving in
September with half-built code **and** an unwritten thesis, which is the worst possible
combination at submission.

**Decision.** Budget allocated as ~40h thesis, ~35h Epic 1, ~35h a minimal tool, ~10h
contingency.

**In scope for the tool:** form → recommendation with a plain-language explanation →
CSV upload → train the recommended method → three or four plots. The full journey,
narrow.

**Deferred to future work:** comparison mode (Epic 5), the benchmark page (Epic 6), the
remaining chart types, the 17-component library, the full accessibility layer, and the
measurement instrumentation of D-009.

**Consequences.** The UX contract is not wasted. `DESIGN.md` and `EXPERIENCE.md` become
the design chapter and the future-work specification — *"the full system was specified
and a justified subset implemented"* is a stronger thesis position than an unspecified
half-built application.

Two cost controls attached to Epic 1:

- **AMLBID gets a four-hour time-box** (#14). It is a 2022 package that may not install.
  If it does not, that becomes a documented limitation rather than a week lost.
- **Subsampling reduced to 2 sizes × 2 seeds** (100 and 400 rows), down from 3 × 3. Still
  covers the band and supports D-006's argument at less than half the compute.

Writing starts in week 2, not week 4. Each benchmark result is written up the day it
appears; reconstructing August's work in September costs double.

---

## D-012 — The recommender ships on heuristics alone; Layer 2 is an upgrade

**Date:** 2026-08-16 · **Status:** accepted · **Affects:** [#2](https://github.com/cecimerelo/ml-sandbox/issues/2), [#15](https://github.com/cecimerelo/ml-sandbox/issues/15), [#17](https://github.com/cecimerelo/ml-sandbox/issues/17)

**Context.** FR-2.1 specifies a hybrid engine, and its Layer 2 depends on Epic 1
finishing. Under D-011's schedule that creates a hard dependency: if the benchmark slips,
the tool has no trained model and there is nothing to demonstrate.

**Decision.** Layer 1 (ISLR heuristics) is built first and works standalone. Layer 2 is
plugged in **if** it arrives in time.

**Consequences.** There is always something demonstrable, which matters when the
supervisor expects a working tool. It also decouples the two halves of the project, so a
delay in the study does not cascade into the application.

If Layer 2 does not land, the thesis reports the heuristic recommender evaluated against
the benchmark — which still answers the research question, since that question is
precisely *whether the pedagogical heuristics hold up empirically*. The hybrid engine
then becomes future work.

---

## D-013 — PMLB becomes the primary source; OpenML is optional validation

**Date:** 2026-08-16 · **Status:** accepted · **Supersedes:** D-002, D-003, D-007 · **Affects:** [#8](https://github.com/cecimerelo/ml-sandbox/issues/8)

**Context.** OpenML's API was unavailable for the whole working session — `504 Gateway
Timeout` on every dataset endpoint, across v1 and v2, from the Python client and from
plain HTTP, reproduced independently in a browser. The web interface kept working because
it runs on a separate search backend.

This is a documented, recurring fault rather than a one-off:

- [openml/openml.org#404](https://github.com/openml/openml.org/issues/404) — *"OpenML API
  returning 504 Gateway Timeout errors"*, opened 2026-07-27. **Still open.** A maintainer
  reported it restored the next day, so individual outages are short — but the underlying
  cause is unresolved and it has recurred.
- [openml/OpenML#1292](https://github.com/openml/OpenML/issues/1292) — 503 on the task
  endpoint, open since 2026-06-02, no activity since the day it was filed.
- Earlier instances closed in 2023 ([#1196](https://github.com/openml/OpenML/issues/1196))
  and 2021 ([#1115](https://github.com/openml/OpenML/issues/1115)).

Outages appear to last days, not months. The problem is the recurrence: with roughly six
weeks to submission (D-011), a dependency that breaks every few weeks can cost days that
are not available.

**Decision.** **PMLB** (Penn Machine Learning Benchmarks) becomes the primary source.
OpenML's CC18 and CTR23 are added as **additional validation if the API recovers in time**
— not as a blocker.

**What PMLB gives.** 450 datasets served from a GitHub repository, so availability follows
GitHub rather than a research server:

| Rows | Classification | Regression |
|---|---|---|
| 50–500 | 75 | 71 |
| 500–10k | 88 | 55 |
| > 10k | 12 | 133 |

Citable as Olson et al. 2017 and Romano et al. 2021. Pinning a commit SHA freezes the
collection permanently, which is stronger reproducibility than OpenML's dataset versioning.

**What it costs.**

- **No predefined splits.** D-003's comparability-with-CC18 argument is forfeited; folds
  are generated under the fold contract instead. This was the original plan, and D-003
  already established it is methodologically sound because every metric is computed within
  a dataset before aggregation.
- A weaker standard-suite citation than CC18 in the AutoML literature.
- Several PMLB datasets originate from UCI and OpenML, so provenance is second-hand.

**Consequences.**

- **D-007 is obsolete.** PMLB carries 146 datasets in the 50–500 row band natively, so
  there is nothing to hand-pick.
- **D-006's subsampling becomes optional.** It is no longer needed for band coverage; it
  survives only as the controlled bias-variance experiment, which is a nice-to-have under
  D-011's schedule.
- Unblocks the study immediately, which under a six-week deadline outweighs the citation
  strength of CC18.

---

## D-014 — Stack: React + MUI frontend, FastAPI backend

**Date:** 2026-08-16 · **Status:** accepted · **Affects:** [#2](https://github.com/cecimerelo/ml-sandbox/issues/2), [#3](https://github.com/cecimerelo/ml-sandbox/issues/3), [#4](https://github.com/cecimerelo/ml-sandbox/issues/4), and the open architecture questions in the epic breakdown

**Context.** The two open stack questions — frontend and backend framework — were blocking
every application epic. Hosting turned out to be the forcing function: the 120-hour budget
in D-011 never included deployment, and free Python hosting (Streamlit Community Cloud,
HuggingFace Spaces) pushes toward a Python-only stack.

**Decision.** **React + MUI** on the frontend, **FastAPI** on the backend, deployed as a
single container on HuggingFace Spaces. This closes both open questions and settles the
chart-rendering question as client-side, which keeps `EXPERIENCE.md`'s per-panel toggles,
tooltips and interaction rules valid.

**Rejected: Streamlit.** Roughly half the hours (~15–20h against ~40h) and near-zero
deployment cost, but it cannot express the interaction model in `EXPERIENCE.md`. The
author chose to honour the UX contract.

Worth recording for the thesis, since it is the honest counter-argument: most of
`DESIGN.md`'s value is portable regardless of framework. That document deliberately keeps
MUI near-stock and spends its budget on the validated chart system — palette, series
slots, facet rules, contrast and colour-vision checks — all of which apply equally to any
plotting library. What React + MUI additionally preserves is the chrome, which was the
deliberately standard part.

**Consequences — the budget does not balance as-is.**

D-011 allotted ~35h to the tool. This stack is estimated at ~40h (frontend ~25h, backend
~10h, deployment ~4h), and estimates under deadline pressure tend to run short rather
than long. Something must give, and deciding *what* now is cheaper than discovering it in
September:

**Resolved the same day: v1 ships two charts instead of four.** Each chart type costs
2–3h once its states and non-visual equivalent are included, so two charts closes the gap.
It is also the cut that costs the thesis least — the chart system is demonstrated as
convincingly by two well-built plots as by four, and the remaining types are already
specified in `DESIGN.md` as future work.

Rejected as the source of the hours: the EDA section (removes one of the three layers the
PRD promises), the contingency buffer (it exists precisely for the unknowns of a first
deployment), and Epic 1 (the research contribution, and the only part that cannot become
future work).

The failure mode being guarded against is unchanged from D-011: arriving in September with
a half-built interface and an unwritten thesis.

---

## D-015 — Missing values are injected, because PMLB has none

**Date:** 2026-08-16 · **Status:** accepted · **Affects:** [#8](https://github.com/cecimerelo/ml-sandbox/issues/8), [#12](https://github.com/cecimerelo/ml-sandbox/issues/12)

**Context.** PMLB's datasets are pre-cleaned: its summary table has no missing-value
column because there are none. But the recommender asks about missing values (FR-1.2,
FR-1.3), the heuristics act on the answer — trees and ensembles cope natively, linear
methods need imputation first — and "handles missing values" is a column of the method
characteristics table (FR-2.2).

Without action, that heuristic would ship untested. Structurally the same gap as the
sub-500-row one: the tool asserting something the study cannot support.

**Decision.** Inject missingness at known rates — **5% and 25% of predictor cells** —
rather than documenting the limitation. Roughly 3–4 hours against a limitations
paragraph, and the author chose coverage.

**How, and why it matters.**

- **The target is never blanked, in either task type.** Removing outcomes changes what is
  being predicted rather than how hard it is to predict, and silently shrinks the
  effective sample.
- **MCAR** — every predictor cell equally likely. The weakest, most neutral assumption.
  Real gaps are often MAR or MNAR, where the pattern itself carries signal; MCAR is
  therefore a floor, and must be stated as one. Methods that fail here will not cope with
  the harder kinds.
- Positions are drawn **without replacement**, so the achieved rate is exact rather than
  approximate.
- Seeded, so a rate comparison is reproducible.

**Consequences.** Each dataset yields three variants (0%, 5%, 25%), so 55 datasets become
165 evaluations. Only *n* changes across the comparison, making the missing-value
sensitivity attributable to missingness alone.

The thesis must state that only MCAR was tested.

---

## D-016 — The collection is bounded by rows at both ends

**Date:** 2026-08-16 · **Status:** accepted · **Revises:** D-005 · **Affects:** [#8](https://github.com/cecimerelo/ml-sandbox/issues/8)

**Context.** D-005 imposed no row ceiling on the benchmark, decided when the largest
candidate had 96k rows. PMLB reaches **1,025,010**. It also descends to **8 rows**, where
five-fold cross-validation leaves under two rows per fold and the score reports the split
rather than the method.

**Decision.** Floor at **50 rows**, ceiling at **100,000**.

D-005's reasoning stands where it applies — the tiered timeouts of FR-8.4 bound the worst
case *per method* — but nothing bounded it *per dataset*, and one million-row dataset
would have consumed more compute than the entire small band.

**Consequences.** The final collection is **55 datasets, 523,531 rows**, spanning 57 to
67,557 rows, with roughly 20 per size band and balanced across task types. All 55 download
and match their declared dimensions.

The application still accepts datasets outside these bounds; the limits are the study's,
not the product's. Above 100k rows the recommender is extrapolating beyond its evidence,
which belongs in the thesis's limitations.

---

## D-017 — Publish the recipe, not the data

**Date:** 2026-08-16 · **Status:** accepted · **Supersedes:** D-010 · **Affects:** [#8](https://github.com/cecimerelo/ml-sandbox/issues/8)

**Context.** D-010 committed to publishing a frozen mirror of the dataset snapshot, so the
study would survive its source disappearing. It also required checking licences first,
since not every dataset permits redistribution — and the client was built to record the
`licence` field for exactly that.

Recording provenance revealed the problem. PMLB publishes a `metadata.yaml` per dataset,
but writes the literal string `None`, or `None yet. See our contributing guide`, where a
field is unfilled. Once those placeholders are treated as absent rather than as values,
**only 9 of the 55 selected datasets have a known original source**.

For the other 46 the licence cannot be checked, because the origin is unknown.
Republishing them would mean redistributing data under terms nobody has verified — not a
risk worth carrying into a thesis for a benefit that can be had another way.

**Decision.** Do not republish the data. Publish the **manifest, the pinned revision, and
the code**.

**Why this loses nothing.** The pinned revision is a commit SHA (D-013), so anyone
re-running `scripts/build_collection.py --fetch` retrieves byte-identical datasets from
PMLB. Reproducibility comes from the pin, not from hosting copies. What a mirror would
have added is insurance against PMLB itself disappearing — real, but bought at the price
of redistributing 46 datasets of unverified provenance.

**Consequences.**

- The licensing check D-010 required is dropped along with the republishing that made it
  necessary.
- The residual risk is stated rather than removed: if PMLB withdraws a dataset or rewrites
  history, the study cannot be reassembled from the manifest alone. The local store under
  `data/datasets/` remains the author's own working copy against that, and is not
  published.
- The thesis's reproducibility claim narrows honestly, from *"here is the frozen
  collection"* to *"here is the exact recipe, pinned to a commit"*.

---

## D-018 — Compute is not the constraint; author time is

**Date:** 2026-08-16 · **Status:** accepted · **Affects:** [#9](https://github.com/cecimerelo/ml-sandbox/issues/9), [#10](https://github.com/cecimerelo/ml-sandbox/issues/10), [#12](https://github.com/cecimerelo/ml-sandbox/issues/12)

**Context.** The method count was about to be cut on an estimate that the full benchmark
would not fit the schedule. `scripts/pilot_timing.py` measured it instead — 8 methods
across 12 datasets spanning every size band, on the actual hardware (M2 Pro, 12 cores).

**Measured.** 44 minutes sequential, 132 with the three missingness variants, **~11
minutes across 12 cores**. The estimate was wrong: the benchmark is an evening, not a
schedule risk.

Cost is also extremely concentrated:

| Methods | Seconds over 12 datasets | Share |
|---|---|---|
| linear, ridge, tree, knn | 9 | 1.6% |
| random forest, boosting, SVM, MLP | 565 | 98.4% |

Two datasets explain most of it: `connect_4` (67k rows, the run's only timeout, on SVM)
and `564_fried` (40k).

**Decision.** Choose the method count on **implementation time**, not compute. Trimming
methods saves nothing measurable unless the four expensive ones go — and those are the
flexible end of the bias-variance spectrum the recommender exists to reason about.

**Consequences.** Cloud compute was investigated and rejected: every free tier is slower
than the author's laptop (Colab ~2 vCPU, Kaggle ~4, HF Spaces ~2, against 12 cores). GPUs
and the Apple Neural Engine do not apply — trees, SVMs, KNN and linear models are
CPU-bound, and none resembles the matrix work accelerators are built for.

FR-8.4's tiered timeouts work as designed: SVM on `connect_4` was cut rather than hanging
the run.

---

## D-019 — Hyperparameters are tuned only where the method requires one

**Date:** 2026-08-16 · **Status:** accepted · **Affects:** [#9](https://github.com/cecimerelo/ml-sandbox/issues/9), [#10](https://github.com/cecimerelo/ml-sandbox/issues/10)

**Context.** The PRD defers tuning to v2, but some methods do not exist without a choice.
Ridge and Lasso need a λ, and there is no sensible default — a poor one zeroes every
coefficient. KNN needs a k, where 1 overfits and n predicts the mean.

**Decision.** Internal cross-validation for the methods that need a hyperparameter to be
defined at all; library defaults for the rest. This is what ISLR does, and what the
literature treats as each method's standard configuration.

**Rejected.** *Fixed values throughout*: arbitrarily penalises the sensitive methods, and
a poor Ridge result would be uninterpretable — the method, or the λ? *Nested CV for all*:
cleanest, and affordable per D-018, but it multiplies the four methods that already carry
98% of the cost.

**Consequences.**

- **The comparison is asymmetric and must be declared.** Ridge competes tuned, Random
  Forest competes on defaults.
- Cheap by accident: Ridge, Lasso and KNN are all in the 1.6% group, so tuning them costs
  roughly 90 seconds in total.
- **A deliberate mismatch with the application.** The study measures each method's
  potential; the application trains on defaults, because tuning inside a request cannot
  fit FR-8.4's timeouts. Layer 2 learns from performance the application does not exactly
  reproduce, and the thesis must say so.

---

## D-020 — Nineteen methods in scikit-learn, two through R, one dropped

**Date:** 2026-08-16 · **Status:** accepted · **Closes:** D-001's open BART question · **Affects:** [#9](https://github.com/cecimerelo/ml-sandbox/issues/9), [#2](https://github.com/cecimerelo/ml-sandbox/issues/2)

**Context.** Cutting the method list looked necessary until the implementation cost was
checked properly: **19 of the PRD's 22 methods are one scikit-learn entry each**,
including several assumed expensive. `SplineTransformer` has shipped since sklearn 1.0,
PCR is a `PCA` + regression pipeline, PLS is `PLSRegression`, polynomial regression is
`PolynomialFeatures`. Implementing them is a table, not three weeks.

**Decision.** Keep the full method list. No cut is needed, because the cost that motivated
one does not exist.

**GAM and BART run through R.** Python's options are weak — `pyGAM` is a partial,
irregularly maintained port, and BART has no solid implementation at all. R has the
reference versions: `mgcv` (Wood) and `gam` (Hastie and Tibshirani, the ISLR authors'
own), plus `dbarts`. Since a bridge is needed for BART regardless, the marginal cost of
routing GAM through it too is small.

**Simple linear regression is dropped.** With datasets carrying 10 to 48 predictors, a
one-variable regression is a deliberately crippled version of multiple regression, not a
competing method. In ISLR it is a teaching chapter, not a contender.

**The bridge is a subprocess, not `reticulate`.** Python writes the data and the fold
assignments, runs an R script, and reads results back in the same schema. The boundary is
a file, which means: the R script can be run by hand when it misbehaves; the fold contract
of D-003 is satisfied literally, since R reads the same file Python wrote; and **if R is
absent the study still runs**, with those two methods recorded as unavailable exactly like
a timeout.

**Time-boxed to four hours**, as AMLBID is. If the bridge does not work in that time, both
methods are documented as absent and the study proceeds on the other nineteen. Two methods
out of twenty-one cannot be allowed to block the schedule.

---

## D-021 — Balanced accuracy and R², both scale-free

**Date:** 2026-08-16 · **Status:** accepted · **Affects:** [#9](https://github.com/cecimerelo/ml-sandbox/issues/9), [#10](https://github.com/cecimerelo/ml-sandbox/issues/10), [#12](https://github.com/cecimerelo/ml-sandbox/issues/12), [#16](https://github.com/cecimerelo/ml-sandbox/issues/16)

**Context.** "Best method per dataset" is the ground truth the entire study rests on, and
the metric defining it had never been chosen.

**Decision.** **Balanced accuracy** for classification, **R² floored at 0** for
regression.

**Why balanced accuracy.** The collection contains real imbalance — one dataset sits at
0.94 — and plain accuracy would rank a majority-class predictor top on exactly those
datasets, producing a ground truth that is wrong where it matters most. Balanced accuracy
is the mean of per-class recall: immune to imbalance, defined for multiclass, bounded
0–1, and equal to accuracy when classes are balanced, so nothing is lost on the easy
cases.

**Why R², and why scale matters more than it appears.** Ranking happens within a dataset,
so scale looks irrelevant — and for top-1 hit rate and Spearman it is. **Regret breaks
this.** It is the performance gap between the recommended method and the best, averaged
across datasets: in RMSE units that means averaging three units of house price with 0.02
of chemical concentration, and the result means nothing. Regret requires a scale-free
metric, which rules out RMSE and MAE.

R² is the standard scale-free choice and the one ISLR uses, so it needs a sentence to
justify rather than a paragraph.

**Rejected.** *ROC-AUC*: needs probabilities, and `SVC(probability=True)` runs internal
cross-validation, multiplying the already most expensive method; multiclass also forces an
averaging choice. *F1-macro*: defensible, but harder to explain than the mean of per-class
recall. *MCC*: most robust, least familiar — it would cost an explanation at the defence
for no gain here.

**Consequences.** R² is floored at 0 so a catastrophic model cannot drag an average
through large negative values; the floor is documented rather than silent. Neither metric
needs predicted probabilities, so the SVM cost stays as the pilot measured it.

---

## D-022 — Missing values are handled the way each method actually handles them

**Date:** 2026-08-16 · **Status:** accepted · **Affects:** [#9](https://github.com/cecimerelo/ml-sandbox/issues/9), [#10](https://github.com/cecimerelo/ml-sandbox/issues/10), [#12](https://github.com/cecimerelo/ml-sandbox/issues/12)

**Context.** D-015 injects missing values to validate the recommender's heuristic that
tree-based methods cope with gaps where others need imputation. The obstacle looked fatal:
if every method has to impute before training, they all receive complete data and the
heuristic cannot be tested at all.

That obstacle was based on a stale belief about scikit-learn. Measured against 1.9:

| Native `NaN` (7) | Requires imputation (9) |
|---|---|
| DecisionTree (clf, reg), RandomForest (clf, reg), ExtraTrees, HistGradientBoosting, Bagging | GradientBoosting, LinearRegression, LogisticRegression, RidgeCV, LDA, GaussianNB, KNN, SVC, MLP |

The split is almost exactly the claim under test — tree-based methods against the rest —
with enough on both sides to conclude something.

**Decision.** Each method declares whether it handles `NaN` natively. Those that do
receive the data untouched; those that do not get an imputer **inside their pipeline**,
fitted per training fold.

**Rejected.** *Uniform imputation for everyone*: fair between methods, but it hands every
one of them complete data and makes D-015 measure nothing. *Imputation for all, measuring
degradation instead*: a real question, but a different one — "who degrades least after
imputation" rather than "who copes with gaps" — and it would have required rewriting the
heuristic the study exists to test.

**Consequences.** This is also what a user actually experiences: someone with gaps who
picks Random Forest imputes nothing, while the same person picking SVM must. The
comparison at 5% and 25% missingness therefore reflects the real choice.

Imputation sits inside the pipeline. Computing a mean over the full dataset leaks test-set
information into training — the failure mode flagged on #10, which does not error, it just
inflates the score.

---

## D-023 — Boosting is the histogram implementation

**Date:** 2026-08-16 · **Status:** accepted · **Affects:** [#9](https://github.com/cecimerelo/ml-sandbox/issues/9)

**Context.** scikit-learn ships two boosting implementations. `GradientBoosting` is the
classic algorithm ISLR describes; `HistGradientBoosting` is the histogram-based variant.
They differ in two ways that matter here: the histogram version is substantially faster,
and it handles `NaN` natively where the classic one does not.

**Decision.** Use `HistGradientBoosting` as the study's boosting method.

**Why.** It lands boosting in the native-missing-values group, which is where ISLR's
reasoning would put a tree ensemble — under D-022 the classic implementation would
paradoxically be a tree method that cannot cope with gaps. It also removes one of the four
methods carrying 98% of the measured cost.

**Consequences.** A deviation from the exact algorithm in the textbook, and the thesis
must state it: the histogram variant approximates the same procedure by binning features,
and is the implementation in general use today.

---

## D-024 — The registry is declarative metadata plus a builder derived from it

**Date:** 2026-08-16 · **Status:** accepted · **Affects:** [#9](https://github.com/cecimerelo/ml-sandbox/issues/9), [#10](https://github.com/cecimerelo/ml-sandbox/issues/10), [#5](https://github.com/cecimerelo/ml-sandbox/issues/5)

**Context.** Methods differ in what they need around them: KNN, SVM, Ridge, Lasso, MLP
and LDA require feature scaling, trees do not; nine of the twenty-one need imputation
(D-022); three need internal cross-validation (D-019). Where that knowledge lives decides
whether a whole class of silent error is possible.

Measured on `adult`, whose features span 0–1 (`sex`) to 12,285–1,490,400 (`fnlwgt`):
**KNN scores 0.6266 unscaled and 0.7468 scaled**, while a decision tree is unmoved
(0.7501 vs 0.7497). Getting this wrong would not produce an error — it would produce a
benchmark concluding that trees beat everything, when what was actually compared was
well-configured methods against badly-configured ones.

**Decision.** The registry holds **declarative metadata** — task compatibility, scaling
requirement, native `NaN` support, tuning strategy — **and builds each method's pipeline
from that metadata**.

**Rejected.** *Metadata only*, with the harness assembling pipelines: leaves it possible
to fit a scaler outside the training fold, which does not raise, it just inflates the
score, and duplicates the assembly logic between study and application. *Pipelines only*:
makes leakage structurally impossible but yields Python objects a React frontend cannot
read, so compatibility information would have to be maintained separately — the same
duplication by another route.

**Consequences.**

- Leakage is **structurally impossible**: nothing assembles a pipeline by hand, and
  scikit-learn guarantees everything inside a `Pipeline` is fitted per training fold.
- The metadata exports to JSON, so the application uses the same table for FR-8.3's
  disabled-with-reason. What the study validates is exactly what the tool offers.
- One source of truth. Metadata and pipeline cannot contradict each other, because one is
  generated from the other.

---

## D-025 — OpenML returns as the primary source; PMLB covers the small band

**Date:** 2026-08-18 · **Status:** accepted · **Supersedes:** D-013 · **Revises:** D-006, D-017 · **Affects:** [#8](https://github.com/cecimerelo/ml-sandbox/issues/8), [#10](https://github.com/cecimerelo/ml-sandbox/issues/10)

**Context.** D-013 moved the study to PMLB after OpenML's API was unavailable for a full
working session. **The API is back** — 200 on both endpoints — and building on PMLB
surfaced a weakness that outweighs the reliability concern: **only 9 of the 55 selected
datasets have a known original source**, because PMLB leaves most provenance fields
unfilled. That is what forced D-017 to abandon publishing the collection, and it is a
thin footing for a thesis that has to say where its evidence came from.

**Decision.** **OpenML-CC18 and OpenML-CTR23 become the primary source.** PMLB supplies
the **sub-500-row band only**, which CC18 excludes by construction.

Each source is used where it is strong:

| | OpenML CC18 + CTR23 | PMLB |
|---|---|---|
| Rows | 500 and above | 50–500 |
| Splits | Predefined, comparable with published work | Generated under the fold contract |
| Provenance | Per dataset, with licence | Sparse |
| Missing values | 9 CC18 datasets carry real gaps | None — pre-cleaned |

**Why.** The author's reason is citation strength: OpenML-CC18 is an established suite in
the AutoML literature, where PMLB is harder to defend. The provenance argument reinforces
it, and real missing values in CC18 complement D-015's injection, which only tests MCAR —
the weakest assumption.

**Consequences.**

- **The reliability risk returns, and is accepted knowingly.** A full day was lost to the
  last outage, [openml/openml.org#404](https://github.com/openml/openml.org/issues/404)
  remains open, and there were incidents in June, 2023 and 2021. The mitigation is D-008:
  download once, then never depend on the service again.
- **D-006's subsampling is needed again** for the controlled bias-variance experiment,
  though no longer for band coverage, since PMLB fills that.
- **D-017 can be revisited.** With OpenML provenance and licences recorded, publishing a
  mirror becomes checkable rather than unverifiable — for the OpenML portion at least.
- **Mixed fold schemes**, deliberately. OpenML datasets use their predefined splits;
  PMLB's get generated ones. Valid because every metric is computed within a dataset
  before aggregation, so a raw score is never compared across datasets (D-003).
- The cost is modest: `Dataset`, `curation`, the stratified sample and the coverage report
  are already source-agnostic, and `openml_client.py` with its retries and cache is still
  in the repository.

---

## D-026 — Layer 2 learns only from measurable dataset properties

**Date:** 2026-08-20 · **Status:** accepted · **Affects:** [#11](https://github.com/cecimerelo/ml-sandbox/issues/11), [#15](https://github.com/cecimerelo/ml-sandbox/issues/15), [#2](https://github.com/cecimerelo/ml-sandbox/issues/2)

**Context.** Layer 2 is a supervised model whose training rows are the benchmark's
datasets. Every input it uses therefore needs a value for each of those 60 datasets. The
three questions FR-1.4 asks of every user do not all have one.

**Explainability importance has no ground truth at all.** There is no such thing as
`credit-g`'s required interpretability — it is what a user needs, not what a dataset is,
and two people with the same data can answer differently and both be right. That column
would be empty in all 60 rows.

**Non-linearity and feature interactions could be measured**, by checking whether
non-linear methods beat linear ones on a dataset. But the user answers them by intuition,
so the model would be trained on measurement and served with guesses.

**Decision.** All three FR-1.4 questions feed **Layer 1 only**. Layer 2 learns from
measurable properties: rows, predictors, task type, feature types, missing-value rate,
class balance.

**Consequences.** The division of labour becomes explicit and defensible: **Layer 2
predicts performance, Layer 1 applies the user's constraints.** A recommendation runs as
*"your data suggests Random Forest would perform best, but you said interpretability is
critical, so here is a decision tree and what it costs you"*.

A third of the always-asked questions therefore do not reach the trained model. That is
worth stating plainly in the thesis rather than leaving a reader to infer it.

---

## D-027 — Layer 2 trains on banded values, not exact ones

**Date:** 2026-08-20 · **Status:** accepted · **Affects:** [#11](https://github.com/cecimerelo/ml-sandbox/issues/11), [#15](https://github.com/cecimerelo/ml-sandbox/issues/15)

**Context.** The benchmark knows `cpu_small` has exactly 8,192 rows. The form offers
bands, so a user reports `500–10k`. Training on the exact figure and serving a band means
serving something other than what was trained: the band has to be turned back into a
number, and 600 rows and 9,000 rows would receive the same answer regardless.

**Decision.** Discretise the benchmark's values into the form's bands before training, so
the model sees the same representation in training and in use.

**Rejected.** *Exact in training, discretised at serve time*: uses more of the
information but leaves a train/serve mismatch that has to be disclosed. *Two models*, one
per path: faithful to both cases, but it splits 60 training rows in half.

**Consequences.** Resolution is lost — 600 and 9,000 rows become the same case. Acceptable
because the form cannot express more than the band anyway, so the lost resolution is
information the deployed system never has.

### On the bands themselves

They were never justified. `< 500 / 500–10k / > 10k` appear in FR-1.3 and again in
FR-8.4's timeout tiers, so the product is at least consistent with itself, but no reason
was recorded — the same pattern as NFR-2's feature cap, which turned out to be right for
the wrong reason.

Checked against the 327 eligible datasets, they split it sensibly: 31% / 56% / 13%, with
the median at 1,000 rows. And **500 has external backing** — it is exactly where CC18's
generator writes `Too small`. **10,000 has none**; it is a round number.

Kept as they are, because the benchmark can settle the question properly. A band is
justified when the winning method changes as it is crossed, and that is precisely what
this study measures. The bands will be checked against the results afterwards, and if
10,000 separates nothing, that is either a documented limitation or a boundary corrected
with evidence — a better argument than choosing a number now by eye.

---

## D-028 — Six meta-features, the ones the form can supply

**Date:** 2026-08-27 · **Status:** accepted · **Affects:** [#11](https://github.com/cecimerelo/ml-sandbox/issues/11), [#15](https://github.com/cecimerelo/ml-sandbox/issues/15)

**Context.** Layer 2 trains on 60 rows, one per dataset. The rule of thumb is roughly ten
observations per feature, which allows five or six before overfitting becomes the dominant
effect. The meta-learning literature in the bibliography — Rivolli 2022, pymfe — offers
dozens: statistical, information-theoretic, complexity, landmarking.

**Decision.** Use exactly the six FR-1.3 supplies: task type, row band, feature-count band,
feature types, missing-value rate, class balance.

**Why this is not merely a compromise.** The application can only ever provide these six.
Any additional feature would have to be computed from the dataset, and the no-dataset path
— the one the tool exists for — could then not use Layer 2 at all. The constraint and the
statistics point the same way.

**Landmarking is excluded by the same decision.** Using cheap models' performance as a
feature is a standard category, but it is not one of the six, it needs a dataset to run
on, and NFR-1 allows under five seconds for a recommendation without one. Its absence is a
documented limitation rather than an oversight.

**Consequences.** A meta-model with 60 rows and 20 features would memorise rather than
learn, and *"you trained a meta-model on sixty points with twenty variables?"* is a
question the thesis would have no answer to. Six keeps that question away, and the model
must be simple and report its uncertainty honestly (#15).

---

## D-029 — AMLBID could not be reproduced; the upper bound is dropped

**Date:** 2026-08-27 · **Status:** accepted · **Affects:** [#14](https://github.com/cecimerelo/ml-sandbox/issues/14), [#16](https://github.com/cecimerelo/ml-sandbox/issues/16)

**Context.** AMLBID (Garouani et al. 2022) was the study's upper-bound comparator — the
published meta-learning recommender against which a heuristic approach could be placed.
D-011 time-boxed the attempt to four hours precisely because a 2022 package might not
still run.

**What was tried.** The package installs and imports cleanly, and its API is intact. It
then fails on the collection's data, for three distinct reasons:

| Failure | Cause |
|---|---|
| `IndexError: single positional indexer is out-of-bounds` | `categ_data.mode().iloc[0]` assumes every dataset has at least one categorical column |
| `ValueError: autodetected range of [nan, nan]` | Histogram-based meta-feature extraction does not tolerate missing values |
| `IndexError: list index out of range`, `KeyError: 'GradientBoostingClassifier'` | Gaps in its own bundled knowledge base |

**Not a version problem.** A separate environment with Python 3.10, pandas 1.x, numpy 1.x
and an older scikit-learn was built to rule that out. The first and third failures persist
there — they are defects in the package, not incompatibilities with current tooling.

**Measured.** Restricting to the cases AMLBID can even attempt — classification, at least
one categorical column, no missing values — leaves 8 of the collection's 30 classification
datasets. **Two of those eight succeed.** Two of thirty overall.

**Decision.** Drop AMLBID. The evaluation compares against the **Random baseline** (#13)
as a lower bound, with no upper bound.

**Consequences.**

- **The comparison weakens, and the thesis must say so.** Beating random is a low bar, and
  without an upper bound there is no evidence about how close the heuristics come to a
  state-of-the-art meta-learner. This is the honest cost.
- **It is a reportable finding rather than an omission.** "A published AutoML baseline
  could not be reproduced" is a result, and a specific one: the failures are named, the
  version hypothesis was tested and excluded, and the success rate is measured.
- The time-box worked. Ninety minutes spent, a clear answer, and the evaluation chapter
  can be planned around a known absence rather than a hope.

An alternative upper bound could be substituted later — a well-tuned strong learner, say —
but it would not be the published comparator the proposal named, and that substitution
belongs in the thesis rather than in a footnote.

---

## D-030 — Datasets are capped at 20,000 rows for evaluation

**Date:** 2026-08-28 · **Status:** accepted · **Revises:** D-016 · **Affects:** [#12](https://github.com/cecimerelo/ml-sandbox/issues/12)

**Context.** The first full run reached 41 of 60 datasets and then slowed to a crawl. All
19 remaining are above 10,000 rows, the largest at 96,320.

The reasoning that allowed this was wrong in a specific way. D-018 concluded that the
tiered timeouts bound the worst case — but **a timeout does not save time, it spends its
whole budget**. SVM is quadratic in sample size, so on 96,000 rows it does not fail fast:
it burns the full 300 seconds on every fold of every variant. That is two and a half hours
for one method on one dataset, and nineteen such datasets turn an evening into days.

**Decision.** Cap every dataset at **20,000 rows** for evaluation, sampled with the run's
seed.

**Why it costs little.** The cap applies identically to every method on a dataset, so it
takes nothing from the comparison between them — it only shrinks the problem. The `>10k`
band and the data-rich regime stay populated, which is what the recommender reasons about.

**Folds are subset, not regenerated.** A row that survives the cap stays in the fold
OpenML assigned it. Regenerating would have swapped the study's published partitioning for
its own on exactly the datasets where comparability with the literature matters most.

**Rejected.** *Letting it run*: fidelity to the original sizes, at the price of days per
run and no ability to correct a mistake — and a study that cannot be re-run is a study
that cannot be corrected. *Lowering the timeout for large datasets*: more timeouts, and
each is a method the study then knows nothing about on that dataset. *Excluding expensive
methods above a size*: would bias precisely the comparison being measured.

**Consequences.** What is lost is fidelity to the exact original size, and the thesis must
say so: results on the largest datasets describe a 20,000-row sample of them, not the
whole. The 41 datasets already evaluated at full size are kept — their rows are recorded,
so the difference is visible rather than assumed.

---

## D-031 — Two baselines: random choice and the single best method

**Date:** 2026-08-28 · **Status:** accepted · **Extends:** [#13](https://github.com/cecimerelo/ml-sandbox/issues/13) · **Affects:** [#16](https://github.com/cecimerelo/ml-sandbox/issues/16)

**Context.** D-029 dropped AMLBID, leaving the study with no upper bound. That makes the
random baseline the only comparator, and beating random is a low bar: *"the recommender
does better than choosing blindly"* is a weak claim to build an evaluation chapter on.

**Decision.** Add a second baseline: **always recommend the method that wins most often
across the collection**, ignoring the user's data entirely.

**Why this is the one that matters.** It answers the question the thesis actually has to
answer — not *"is this better than random?"* but **"is there any point looking at the
user's data at all?"** If a recommender that inspects the problem cannot beat one that says
"use Random Forest" to everybody, personalisation is not earning its complexity, and that
is worth knowing before the defence rather than during it.

It is also standard in the meta-learning literature for exactly this reason.

**Both are free.** Neither trains anything. A baseline picks a method name and looks up the
score that method already recorded on that dataset — arithmetic over the benchmark's
results table. That is why the benchmark stores every method on every dataset rather than
only the winner: without it, *"what would have happened had I chosen X?"* is unanswerable.

The recommender is evaluated the same way, so all three are measured by the same procedure
over the same numbers.

**Consequences.** The random baseline can be repeated over many seeds and reported as a
distribution rather than a single draw, since a repetition costs a table lookup.

### Settled the same day

**A random draw skips methods that error on that dataset.** Counting a failure as a zero
would have made random look worse and the recommender better by comparison — a bias a
committee would be right to point at. It is also unrealistic: a user who picked QDA and saw
an error would try something else rather than give up. Random competes only against methods
that ran, which is the harder and fairer bar.

**A thousand repetitions**, reported as a mean with an interval rather than a single
figure. One draw is noise, and a repetition costs a table lookup. Reporting *"random
reaches 0.52 ± 0.04"* rather than *"random reached 0.49"* keeps the comparison from
resting on an accident of the seed.

---

## D-032 — Basis expansions are bounded by the width of the data

**Date:** 2026-08-29 · **Status:** accepted · **Affects:** [#9](https://github.com/cecimerelo/ml-sandbox/issues/9), [#12](https://github.com/cecimerelo/ml-sandbox/issues/12)

**Context.** The benchmark stalled indefinitely on `brazilian_houses` — CPU at 100%, no
results written, no timeout fired. The method was polynomial regression.

The dataset has 9 columns, but one-hot encoding expands them to 34. A degree-3 polynomial
over 34 features produces **7,770 columns**, a 0.7GB matrix rebuilt on every inner fold of
the tuning search. More columns than the data has information to support, and slow enough
to look like a hang.

**Why the timeout did not save it.** That fit is a single long numpy call, and
`signal.alarm` delivers between Python instructions. The budget never fired. This is a real
limit of the sequential, signal-based design chosen for #10: it interrupts Python, not C.

**Decision.** Choose the degree from the input width at fit time, keeping the expansion
under **2,000 columns**. Prevention rather than interruption, because interruption
demonstrably does not work here.

`brazilian_houses` went from hanging indefinitely to fitting in 0.5 seconds, with degree 2
selected instead of 3.

**Consequences.**

- **A known limitation is now documented**: signal-based timeouts cannot interrupt a long
  call inside a C extension. Anything capable of one long call has to be bounded by
  construction. Nothing else in the registry currently is, but a future addition might be.
- Polynomial results computed under the old unbounded grid were discarded — 450 rows — so
  the collection is not scored under two different definitions of the same method.
- The smallest degree always survives the filter: a grid with nothing in it would fail
  rather than degrade, and a basis expansion that expands nothing is not one.

---

## D-033 — Layer 2 predicts relative performance, not the winner

**Date:** 2026-08-29 · **Status:** accepted · **Affects:** [#15](https://github.com/cecimerelo/ml-sandbox/issues/15), [#16](https://github.com/cecimerelo/ml-sandbox/issues/16), [#2](https://github.com/cecimerelo/ml-sandbox/issues/2)

**Context.** The obvious target — "which method wins" — is not well defined. The
one-standard-deviation tie rule means most datasets have several winners, so a
single-label classifier would be taught that `boosting` is *wrong* on a dataset where it
tied with the best. It would be penalising correct answers.

**Decision.** Layer 2 is a **regression over (dataset, method) pairs**, and its target is
**performance relative to the best method on that dataset** — negative regret.

**Why regression rather than classification.**

- **FR-2.2 needs three ranked alternatives**, not one pick. Predicted scores give an order
  directly; a classifier's ranking would have to be invented.
- **Ties stop being a problem.** Methods that tie have near-identical targets, which is the
  truth, rather than one being labelled correct and the rest wrong.
- **Sixty training rows become about nine hundred** — 60 datasets by 15 methods — which
  changes the overfitting picture D-028 was written under. Seven meta-features against 900
  rows is a different proposition from seven against 60.

**Why relative rather than raw score.** A balanced accuracy of 0.70 can be excellent on a
hard dataset and mediocre on an easy one. Trained on raw scores, the model spends much of
its capacity learning **which datasets are easy** — information that is useless at
recommendation time, since only the ordering *within* a dataset ever matters.

Subtracting the best score per dataset removes that dimension. An easy dataset and a hard
one look the same when the spread between methods is the same, which is correct: the
recommendation should be the same.

**Consequences.**

- The prediction is directly interpretable as *"how much you lose by choosing this"*, which
  the explanation layer can state to a user without translation.
- Validation must group by dataset. A random split would put the same dataset in training
  and test, and the model would recall its scores rather than generalise — inflating every
  number reported.

---

## D-034 — Layer 1 belongs to the study, not the application

**Date:** 2026-08-29 · **Status:** accepted · **Moves work from:** [#2](https://github.com/cecimerelo/ml-sandbox/issues/2) · **Affects:** [#16](https://github.com/cecimerelo/ml-sandbox/issues/16), Epic 1

**Context.** #16 requires the research metrics to compare four approaches, the first being
**heuristics only**. Layer 1 was scoped into Epic 2 with the application — the epic reduced
under D-011.

That is the wrong place for it. The thesis's secondary objective is *whether the
pedagogical heuristics hold up empirically*, so Layer 1 is not a feature of the tool: **it
is the object of study.** The benchmark says what actually won; Layer 1 says what the
textbook predicts. Without both written down there is nothing to compare, and the study
cannot answer the question it exists for.

The difference in what the thesis can claim:

| Without Layer 1 | With Layer 1 |
|---|---|
| *"A trained model predicts which method performs well"* | *"The heuristics taught in class are right X% of the time; a model trained on data reaches Y%; always picking one method reaches Z%"* |

The first is another meta-learning exercise. The second is the contribution.

**Decision.** Layer 1 moves into Epic 1 and is implemented before #16.

**Consequences.** It is cheap — twelve rules over the same seven meta-features, not a
system. Each rule carries the claim it encodes in the words a user is shown, which is also
the sentence the thesis quotes when reporting whether that claim survived.

The two user inputs that reach it — required interpretability and suspected non-linearity —
are constraints and beliefs rather than measurable properties, which is why they arrive
here and never in the trained model (D-026).

**A rule that turns out to be wrong is a result.** Nothing in the reporting is arranged to
avoid that conclusion: if the heuristics do not predict performance, that is worth knowing
and worth stating, and the per-rule structure makes it possible to say *which* claims failed
rather than only that the set did.

---

## D-035 — Explainability is a property of the method, on three levels

**Date:** 2026-08-29 · **Status:** accepted · **Affects:** [#16](https://github.com/cecimerelo/ml-sandbox/issues/16), FR-1.4, FR-2.2

**Context.** The hybrid strategy needs to know which methods a user's explainability
requirement rules out. The obvious move — a list of opaque methods inside Layer 1 — is
wrong twice over.

It duplicates. The rule `interpretability-rules-out-black-boxes` already names those
methods, so a second copy means two places to update when a method is added. **When they
drift, nothing fails:** the ranking penalises a method for being opaque while the filter
lets it through, and the output is coherent and wrong.

And it is the wrong home. Whether a method can be explained is a property *of the method*,
like `handles_nan` or `needs_scaling`. The registry is where those live, it is already
declared rather than implied, and the application already reads it.

**Two explanations, easily conflated.** The tool always explains **why it recommended a
method** — from theory, for every method, opaque ones included. That never stops working.
This field is about something else: whether the user, having deployed the model, can
justify **an individual prediction** to the person it affects. *An explainable recommender*
and *a recommender of explainable models* are separate properties, and only the second is
what the constraint restricts.

**Decision.** `Method.explainability`, one of three levels.

| Level | Meaning | Count |
|---|---|---|
| `readable` | The model *is* the explanation — a tree's path, a linear model's weights | 8 |
| `with effort` | Recoverable but needs translating — KNN's neighbours, a GAM's curves | 7 |
| `opaque` | No single reason exists — three hundred trees voting | 6 |

Declared per method, not derived from `family`: `trees` holds both the decision tree and
the random forest, `svm` both the linear and the RBF kernel.

**Three levels because the form asks for three.** FR-1.4 offers *not important / somewhat /
critical*, and with a binary field `somewhat` behaves exactly like `not important` — the
user answers a question that changes nothing, which is worse than not asking. The scales
now line up: `somewhat` drops the opaque, `critical` also drops what takes effort.

**Post-hoc attribution is not counted.** SHAP and LIME give per-case attributions for a
forest and are widely used, so this is a position rather than a fact. They fit a simple
surrogate near one point and explain *the surrogate*; where it fits badly the explanation
is plausible and wrong, with nothing to signal which happened. For a tool whose purpose is
justified recommendations, that is the wrong side of the line.

**Exclusions are returned, never silently dropped.** A recommender that quietly withholds
the best method leaves the user unable to see what the constraint cost them. The caller
reports the gap — *"a random forest would score 0.08 higher, but you could not explain its
decisions"* — and the choice stays with the person who set the constraint. Aggregated over
the collection, that gap is **the cost of requiring interpretability**, which is a result
the memoria can report rather than an interface detail.

**Consequences.** `INTERPRETABLE` in Layer 1 grows from four methods to eight, since ridge,
lasso, naive Bayes and the linear SVM are all readable — the hand-written list was simply
under-inclusive. That overlap exposed a latent scoring bug: rules built as
`INTERPRETABLE + REGULARISED` named ridge twice and would have paid it the weight twice,
with its claim shown twice in the explanation. Rules now deduplicate on construction.

---

## D-036 — Report the strategies on two strata, because pooling hides the answer

**Date:** 2026-08-29 · **Status:** accepted · **Affects:** [#16](https://github.com/cecimerelo/ml-sandbox/issues/16)

**Context.** The first run of the comparison produced a table that read as a null result:
every strategy within a few points of every other, the trained model barely ahead of
*"always recommend the same method"*.

One number gave it away. **Random choice hit top-3 on 75% of datasets.** Choosing three
methods at random out of fifteen should not find the best one three times in four.

The cause is in the results, not the code. Averaged over the collection, **5.2 of the 14.1
methods that run tie with the best** under the 1-standard-deviation rule (D-031) — 37% of
the catalogue. On `schizo`, all fourteen tie. With a third of methods winning, three drawn
at random contain a winner 77% of the time, which is the observed figure to within noise.

So the pooled metric was largely measuring **how often the question has no wrong answer.**
Datasets where anything works hand an identical hit to all five strategies and dominate the
average, compressing everything toward the middle.

**How much it hid**, on the 44 datasets available when this was found:

| Strategy | Pooled | Where the choice matters |
|---|---|---|
| Learned (Layer 2) | 0.59 | **0.57** |
| Single best method | 0.59 | **0.33** |
| Heuristics (ISLR) | 0.41 | 0.24 |
| Random choice | 0.36 | 0.10 |

The recommender's margin over the baseline that ignores the user's data goes from **2
points to 24**. The pooled table supports "there is no point looking at the user's
problem"; the narrowed one refutes it. Both come from the same results.

**Decision.** Report both strata, always. A dataset is *discriminating* when at most
`TOP_K` methods tie for best.

**The threshold is `TOP_K`, not a tuned number.** The interface shows three alternatives,
so where more than three methods are best, a user following the tool cannot land wrong —
there is nothing for a strategy to get right. Tying it to the interface means it cannot be
quietly adjusted until the results improve.

**Both, not one.** The pooled figure alone understates every margin. The narrowed figure
alone looks like a subset chosen to flatter. Together they answer two different questions:
*how often does the recommendation matter?* and *when it matters, is it right?* — and the
first is itself a finding worth reporting, since roughly half the collection turns out not
to need a recommender at all.

**Consequences.** Narrowing applies to **scoring only**, never to training. A deployed
recommender learns from every dataset it has, easy ones included, so training only on the
hard ones would measure a system nobody would build. Tested.

---

## D-037 — The application stack, and why most of it was already decided

**Date:** 2026-08-29 · **Status:** accepted · **Unblocks:** [#2](https://github.com/cecimerelo/ml-sandbox/issues/2), [#3](https://github.com/cecimerelo/ml-sandbox/issues/3)

**Context.** Both application epics were labelled blocked on architecture. Most of that
block was illusory: Layer 1 and Layer 2 are Python, and a recommender whose engine cannot
be called from the server is not a design option. The frontend was settled earlier — a
simple interface in MUI, so React.

| Layer | Choice | Why it was not really open |
|---|---|---|
| Backend | FastAPI | The engine is Python. Anything else means serving the model over a second hop, or reimplementing Layer 1 in another language and letting the two drift. |
| Frontend | React + MUI | Already chosen. MUI supplies the form controls, the collapsible sections and the accessible defaults this interface is mostly made of. |
| Session storage | SQLite | FR-7.3 stores one anonymised row per session — a few hundred, not a few million. A database server is infrastructure to run, back up and explain, for a table that fits in a file. |
| Charts | Recharts, client-side | The real decision. |

**The charts were the genuine choice.** Rendering them server-side as matplotlib images is
faster to write in a language already in use, and it was tempting for that reason alone.
It also removes hover and the *"view as table"* toggle — FR-3 asks for both — so choosing
it means re-scoping Epic 3 rather than building it.

There is a privacy argument too. **FR-7.2 says uploaded datasets are processed in memory
and never written to disk.** Server-rendered charts sit awkwardly beside that: the image is
derived from the user's data, and every rendering pipeline worth its name writes temporary
files. Sending aggregates the client draws keeps the raw data on the server for exactly the
length of one request, which is what the privacy notice claims.

**Decision.** FastAPI · React + MUI · SQLite · Recharts drawing client-side from aggregates
computed server-side.

**Why FastAPI and not Flask or Django.** The study's type registry is already pydantic:
`MetaFeatures` is a `StrictModel` with `extra="forbid"` and bands typed as
`Literal["<500", "500-10k", ">10k"]`. Under FastAPI **that class is the request schema**,
so a form answer the model never saw is rejected at the edge, naming the field, with no
validation written by hand.

That matters more here than it usually would. D-027's train/serve agreement is held up by
those types, and it has already failed once — `regime` computed two ways gave `moderate` on
one path and `data-rich` on the other. An API carrying its own copy of the schema is a
second place to define what a valid band is, and **when the two drift the model does not
error, it predicts.** Flask would work; it would mean writing that validation by hand, or
adding pydantic to it, which is rebuilding a worse FastAPI. Django brings an ORM, an admin
and migrations for five endpoints and one SQLite table.

**Rejected: Streamlit, and what rejecting it costs.** Streamlit or Gradio would remove the
frontend entirely — no React, no build step, no endpoints — and save roughly thirty of the
ninety-eight estimated hours. Given the schedule, that is precisely the margin the memoria
is short of, so this was a real option and not a straw man.

It was rejected because it cannot deliver the design that already exists. `EXPERIENCE.md`
and `DESIGN.md` specify named MUI components (a non-sticky `AppBar`, an `Accordion`
collapsed by default, one-level `Dialog`s), a thirteen-row load-bearing accessibility
register, and a chart behaviour contract with a view-as-table toggle and text equivalents
per plot family. Streamlit supplies none of the three. Choosing it turns the UX work into
an appendix describing an interface that was never built, rather than into the product.

**Rejected: Streamlit first, React if time allows.** The prudent-sounding option, which in
practice means maintaining two interfaces, or shipping the first one without the polish
that was deferred to the second.

**Consequences.** The EDA endpoints return summaries — bin counts, correlation matrices,
quartiles — never rows. That constrains the API in a useful direction: an endpoint that
cannot return the raw data cannot leak it by accident.

**Scope, recorded because it was raised and decided against.** With roughly ninety hours
left before submission and the memoria still to write, Epic 2 and Epic 3 in full consume
the whole budget. The alternative offered was Epic 2 complete with Epic 3 reduced to the
upload-and-detect path, dropping the EDA layer, which demonstrates nothing the thesis
argues. **Both epics in full was chosen deliberately.** The tasks below are sequenced so
that each stopping point leaves something coherent — if time runs out, what exists still
works, rather than being half of everything.
## D-038 — An orange top bar, against the design's own advice

**Date:** 2026-08-29 · **Status:** accepted · **Amends:** D-037 · **Affects:** [#32](https://github.com/cecimerelo/ml-sandbox/issues/32)

**Context.** `DESIGN.md` is emphatic that the product has **no brand colour**: MUI's default
light theme *is* the design, the top bar is white on a divider hairline, and the entire
design budget is spent on the charts. The author asked for a coloured bar anyway.

**Decision.** Deep orange 900, `#bf360c`, white text.

**Two constraints made the choice, not taste.**

The obvious orange is the one already in the product — `series-2` `#eb6834`. It fails
twice. It is **3.20:1**, so white text on it does not clear AA at all. And it is a **chart
slot**: using it as chrome would make the app's furniture the same colour as *"the first
alternative the user selected"* in every plot. The palette already keeps chrome blue one
step darker than `series-1` precisely so chrome and marks are never confusable, and going
orange must not reintroduce that from the other side.

| Candidate | White text on it | |
|---|---|---|
| `#eb6834` `series-2` | 3.20:1 | fails, and collides with a data slot |
| `#e64a19` deep-orange 700 | 3.92:1 | fails |
| `#d84315` deep-orange 800 | 4.44:1 | fails, narrowly |
| **`#bf360c` deep-orange 900** | **5.60:1** | **adopted** |

Only one orange clears AA, and it clears it by being dark enough to read as furniture
rather than as a mark — which is the same property that keeps it away from `series-2`.
It is also a stock Material value, so the file keeps its posture of inventing no colours.

**Consequences.** The bar drops its divider hairline: a coloured bar separates itself from
the page, and the rule the white version needed would be drawing a line already there.

Three tests hold the reasoning rather than the result: white text clears 4.5:1, the bar's
hex is not any series slot, and it sits at least 2 contrast points away from `series-2`.
A future adjustment toward a friendlier, lighter orange fails them, which is the point —
the failure mode here is drifting back toward the colour that looks nicer and cannot be
read.

**Not revisited:** the rest of the chrome. This is one deviation, not permission for a
brand system — which is the elaborate thing `DESIGN.md` ruled out and the reason it says
there is no brand colour in the first place.

---

## D-039 — Three-option beliefs, and what `unsure` does

**Date:** 2026-08-29 · **Status:** accepted · **Extends:** D-035 · **Closes:** [#35](https://github.com/cecimerelo/ml-sandbox/issues/35)

**Context.** FR-1.4 asks the user three questions and offers three answers to each. Two of
them reached an engine that could not hear the middle one.

**Feature interactions** were not consumed at all: `MetaFeatures` has seven fields and none
is interactions, so the form would have asked a question that changed nothing.
**Non-linearity suspicion** was worse, because it looked implemented — `suspects_non_linearity`
was a `bool`, so `unsure` and `no` were the same value and produced the same recommendation.

This is D-035's fault a second and third time: a three-option control with two-option
behaviour. It is worth naming as a pattern, since it has now appeared in every place the
form and the engine meet.

**Decision.** Both become `Suspicion = Literal["no", "unsure", "yes"]`, scaled by
`SUSPICION_STRENGTH = {no: 0.0, unsure: 0.5, yes: 1.0}`, and two rules answer the
interaction question.

**Why `unsure` tilts rather than abstains, and tilts toward flexibility.** The cost of
being wrong is **asymmetric**. Assume additivity when the truth is not additive, and a
linear model cannot recover — the surface it needs is not in the space of functions it can
fit. Assume flexibility when the truth is additive, and a flexible method can still
represent a line: it pays variance for the privilege, but it gets there. Under genuine
uncertainty the recoverable error is the one to prefer.

**Half rather than full**, because a hedge that moves as far as a conviction is not a
hedge, and `unsure` would be indistinguishable from `yes` — the same defect in a new
costume.

**The claim does not change with the user's confidence, only its weight.** Scaled rules are
copies: same name, same sentence. Rewording an explanation because the user was unsure
would make the tool's reasoning depend on the user's confidence, which is not something the
textbook has an opinion about.

**Which methods.** `FINDS_INTERACTIONS` — trees, and the kernels and hidden layers that
reach the same place by another route. A tree's second split is conditional on its first,
which is what an interaction *is*.

`ADDITIVE` — linear, logistic, LDA, GAM, naive Bayes. Additive by construction rather than
by accident: a GAM's entire form is a sum of per-feature curves, and naive Bayes assumes
conditional independence, **which is the interaction assumption negated**. They can
represent a joint effect only if a person works out which one matters and writes the
product term in by hand.

**Consequences.** The two beliefs stay separate questions because they are separate claims:
a curved relationship in one variable is not a joint effect between two, and splines bend
while remaining additive. Passing a boolean now raises rather than being silently coerced —
`True` is not an answer the user could have given.

## D-040 — A glossary, against the spine's own rule

**Date:** 2026-08-29 · **Status:** accepted · **Amends:** `EXPERIENCE.md § The Explanation Layer` · **Affects:** [#39](https://github.com/cecimerelo/ml-sandbox/issues/39)

**Context.** The experience spine rules this out in as many words:

> **No progressive disclosure of education.** There is no "learn more", no expandable
> glossary, no tour, no first-run coach marks. A wizard was rejected upstream; a tutorial
> layered on top of a dashboard is the same rejected idea wearing a coat.

And FR-1.6's explanations are *"always visible. Never behind a tooltip or icon."*

The author asked for one anyway, having watched copy get worse to avoid words it could not
use. That is a real cost: *"catching quirks that happen to be in the rows you have and will
not repeat"* is what a sentence becomes when it may not say **noise**.

**Decision.** A glossary, with the two objections answered by construction rather than by
declining to build it.

**Objection 1 — you have to know that you don't know.** A definition behind an unmarked
word only reaches a reader who already suspects the word. Someone who reads *noise* as
loud sounds has no reason to hover. **So glossed terms are visibly marked** — a dotted
underline, present before any interaction. That is the whole difference between a glossary
and a trap, and it is why this is not the progressive disclosure the spine rejected: the
reader is told the explanation exists rather than left to discover it.

**Objection 2 — hover does not exist on touch or keyboard.** `Term` opens on hover, on
focus **and** on tap, and carries `aria-describedby` regardless of whether the popup
appears. Putting the definition out of reach of a phone or a keyboard would be a strange
thing to do to the one part of the interface that exists for people who are stuck.

**The unexpected gain.** The catalogue's jargon rule stops being a blocklist and becomes a
completeness check: a term of art may appear **if and only if** it is marked for the
glossary. That is strictly stronger. A blocklist only catches the words someone thought to
list, and silently permits every term nobody remembered.

**Markers live in the copy, not in components.** `{{noise}}` inside a plain string keeps
the catalogue readable as writing — a supervisor has to review it as content (D-039's
requirement), and a file of JSX is not writing.

**Consequences.** Definitions obey the copy's own constraints: citation-free, one or two
sentences, and not leaning on a second undefined term. All three are tested. FR-1.6 is
untouched — the form explanations stay always-visible prose; the glossary marks terms
*inside* them rather than replacing them with a link.

**What was rejected.** Restricting the glossary to unavoidable vocabulary — method and
metric names, which the product cannot not use — leaving concepts written around as before.
Narrower and fully compatible with the spine. Overruled by the author in favour of the
general form.
---

## D-041 — The outcome is declared, never guessed

**Date:** 2026-08-30 · **Status:** accepted · **Affects:** [#12](https://github.com/cecimerelo/ml-sandbox/issues/12), [#16](https://github.com/cecimerelo/ml-sandbox/issues/16), [#43](https://github.com/cecimerelo/ml-sandbox/issues/43)

**Context.** `split_target` fell back to the last column when none was named `target`, on
a comment that read *"PMLB names every outcome `target`; OpenML puts it last."* The second
half is false. OpenML declares `default_target_attribute`, and **five of the forty OpenML
datasets put the outcome somewhere else.**

| dataset | real outcome | what was used |
|---|---|---|
| `kings_county` | `price` | `date_day` |
| `cps88wages` | `wage` | `parttime` |
| `diamonds` | `price` | `z` |
| `fifa` | `wage_eur` | `goalkeeping_reflexes` |
| `space_ga` | `ln_votes_pop` | `ycoord` |

**It did not fail.** Every method on `kings_county` scored R² between 0.00 and 0.04, which
reads as a hard dataset. The bug surfaced only because KNN happened to raise — it stores
its training targets and averages them at prediction time, so a categorical target became
`str / int`. Every other method coerced or scored around it silently.

`space_ga` shows how well it hid: the false target `ycoord` is a spatial coordinate,
partly predictable from the other coordinates, so it produced R² around 0.5. A plausible
number is a better disguise than a bad one.

**Decision.** `load_any` renames OpenML's declared target to `target`, and `split_target`
**raises** when no such column exists.

**No fallback, deliberately.** A guess that is usually right is worse than an error here,
because nothing downstream can tell a wrongly-chosen target from a genuinely difficult
problem. The study reports the second when it has the first.

**What it cost.** 1,350 rows deleted and recomputed — `kings_county`, `fifa`, `space_ga`.
`cps88wages` and `diamonds` were still queued and were never computed wrongly, because the
run was stopped. The previous results are kept as
`results-*.parquet.before-target-fix` for the comparison below.

**The correction on `space_ga`, at 0% missingness:**

| method | wrong target | right target |
|---|---|---|
| mlp | 0.000 | **0.663** |
| svm_rbf | 0.000 | **0.688** |
| svm_linear | 0.000 | **0.571** |
| boosting | 0.548 | 0.710 |
| linear_regression | 0.032 | 0.326 |

**The ranking changed, not only the level.** Before: boosting > random forest > KNN. After:
boosting > SVM-RBF > splines. The winner set differs, so every hit rate in #16 was computed
against the wrong answer on these datasets.

**A signal that was there and was not read.** Three methods scoring *exactly* 0.000 is not
a result — R² is floored at zero (D-018), so three exact zeros mean three methods did worse
than predicting the mean. Worth treating as a symptom rather than a row in a table.

**Consequence for the application.** FR-1.2 already has the user pick the target, and the
spine makes it the form's only sequential dependency. That requirement now rests on
evidence rather than instinct: **the half of the system that guessed is the half that
broke.** Recorded on #43, with the sharper corollary — the target control must not come
pre-filled, because a suggested default is confirmed without being read, which reintroduces
the guess with a human as its alibi.

`scripts/check_targets.py` checks the whole collection, since the failure is silent and a
unit test cannot load sixty datasets.

---

## D-042 — The middle explainability level, in the ranking as well as the filter

**Date:** 2026-08-30 · **Status:** accepted · **Completes:** D-035 · **Affects:** [#36](https://github.com/cecimerelo/ml-sandbox/issues/36)

**Context.** Found by the author trying to answer their own form: *"I don't get how these
questions affect anything."* They were right, and about the worst possible person to have
to ask — if the person who specified the question cannot see its effect, nobody can.

**Two faults, one introduced by a partial fix.**

D-035 made explainability three-valued and added `excluded_by_constraints`. The field, the
form and the filter all took three levels. **`applicable_rules` still asked
`== "critical"`.** So in the ranking the user actually sees, `somewhat` behaved exactly
like `not important` — the defect D-035 exists to fix, left alive in the one path that
shows. That is the third appearance of this pattern, and the first I caused.

The second is subtler and only visible by looking. **Scaling both interpretability rules
by the same factor cannot reorder anything**: readable methods rise and opaque ones fall
whatever the factor, so `somewhat` and `critical` produce identical orderings however far
apart their weights sit. Making the middle level "half strength" fixes nothing on its own.

**Decision.** `EXPLAINABILITY_STRENGTH = {not important: 0.0, somewhat: 0.5, critical: 1.0}`,
**and** `recommend` applies the constraint filter itself rather than leaving it to the
caller.

What actually separates the two levels is **what each rules out**, not how hard it pushes:
`somewhat` drops the opaque, `critical` also drops what takes effort. That distinction has
to reach the ordering to exist at all.

```
suspected non-linearity, which lifts KNN — a `with effort` method
  somewhat   decision_tree · knn · lasso · naive_bayes
  critical   decision_tree · lasso · naive_bayes · ridge
```

**They still agree when the constraint does not bind**, and that is correct rather than a
remaining defect: if nothing costly was going to be recommended, ruling it out changes
nothing. Tested both ways, so neither the agreement nor the difference can quietly go away.

**Excluded methods are ranked last, never dropped** — withholding the best option silently
leaves the user unable to see what their constraint cost them.

**What this does not fix.** The other two questions still rarely move the visible top three:
a "yes" on non-linearity lifts six methods by the same amount, and the alphabetical
tie-break then returns the same leaders. The engine did something; the user cannot see it.
That is partly a real finding — **the textbook's heuristics are coarser than they look**,
which is the study's own subject — and partly a presentation problem for the recommendation
panel, which has to show that several methods are tied rather than implying a ranking it
does not have. Recorded on #37 rather than papered over here.
