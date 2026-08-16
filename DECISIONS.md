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
