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
