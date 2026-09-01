# Findings

What the study measured, as it was measured. Separate from `DECISIONS.md`, which records
choices and their reasoning: a decision can be argued with, a finding can only be
reproduced or refuted.

Written down rather than left in a parquet file, because a result nobody records is a
result that gets remembered as whatever the memory prefers — usually more flattering than
what happened.

Each entry names the run it came from, so a number can be traced to the bytes that produced
it.

---

## F-001 — The benchmark, and what the four strategies achieved

**Date:** 2026-08-31 · **Run:** `results-801f29e62585.parquet` · **Closes:** [#12](https://github.com/cecimerelo/ml-sandbox/issues/12) · **Answers:** [#16](https://github.com/cecimerelo/ml-sandbox/issues/16)

**22,500 evaluations, 60 datasets, 20 methods, 12 hours.** 551 unscored (2.4%): QDA on
singular covariances, Lasso timing out under `saga` on wide data, and the 90 refusals
`polynomial_interactions` was predicted to produce (D-046).

### Every dataset

| Strategy | Hit | Top-3 | Regret |
|---|---|---|---|
| Learned (Layer 2) | 0.58 | 0.77 | **0.040** |
| Hybrid | 0.58 | 0.77 | 0.040 |
| Single best method | 0.57 | 0.75 | 0.044 |
| Heuristics (ISLR) | 0.35 | 0.72 | 0.113 |
| Random choice | 0.27 | 0.55 | 0.271 |

### Where the choice makes a difference (29 datasets)

Datasets where at most three methods tie for best (D-036). The other 31 hand a hit to every
strategy alike, and pooled they hide most of the difference.

| Strategy | Hit | Top-3 | Regret |
|---|---|---|---|
| Single best method | **0.45** | 0.69 | 0.038 |
| Learned (Layer 2) | **0.45** | 0.69 | **0.028** |
| Heuristics (ISLR) | 0.24 | 0.55 | 0.134 |
| Random choice | 0.03 | 0.31 | 0.342 |

## Four findings, and the first is the uncomfortable one

**A trained model does not pick the winner more often than a fixed choice.** 0.45 against
0.45. This is the question D-031 was written to force, and the answer is that inspecting
the user's problem does not improve *how often you are right*.

**It does improve how much you lose.** Regret 0.028 against 0.038 — **26% less performance
given up**. Layer 2 misses as often and misses by less. Reported with hit rate alone it
would look worthless, which is why D-031 required both.

**ISLR's heuristics are clearly beaten.** 0.24 against 0.45, with three times the regret.
Far better than chance (0.03), so they carry real signal — and *"always use what usually
wins"* beats them comfortably. **This is the thesis's secondary objective, answered, and
the answer is no.**

**Requiring explainability costs +0.117 regret and binds on all sixty datasets.** The best
available method is always an opaque one. Not usually — always.

## The fixed baseline is itself a result of this study

It is *"always Gradient Boosting"*, best on **36 of 60** datasets. Nobody knew that before
this benchmark measured it.

A practitioner without the study is not at 0.45, they are at **0.03**. The study did not
fail to beat a trivial comparator; **it produced the comparator**, and the comparator turned
out to be strong. What the benchmark delivers is the identity of the fixed best method
rather than a personalised choice — a finding about the problem, not a shortfall of the
tool.

Methods reaching the winning set most often, of 60 datasets:

| Method | Best on |
|---|---|
| Gradient Boosting | 36 |
| Random Forest | 34 |
| Neural Network (MLP) | 28 |
| Bagging | 27 |
| Ridge | 21 |

## What makes these numbers worth anything

The apparatus, not the numbers. Leave-one-dataset-out for **every** strategy including the
ones that do not learn (D-036); the leak found and removed from the fixed baseline, which
had been choosing its method while looking at the dataset it was about to be scored on; the
one-standard-deviation tie rule applied identically everywhere; both metrics reported
because either alone tells a different story.

A study whose result is *"the sophisticated thing does not beat the simple thing"* is worth
more than one that avoids finding out.

## Not yet established

**Whether Layer 2 wins in an identifiable regime** — few rows, high dimensionality, heavy
missingness. If such a subset exists the finding becomes *"ties overall and wins where X"*,
which is more useful than either half alone.

**How stable the 29-dataset stratum is.** Small enough to want an interval rather than a
point estimate. An earlier partial run put the same comparison 15 points elsewhere.

**Anything about missing data.** Every figure above is at 0% missingness. The 5% and 25%
variants were computed and have not been looked at.
