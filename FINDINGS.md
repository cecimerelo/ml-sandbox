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

**Date:** 2026-08-31 · **Run:** `results-801f29e62585.parquet`, 60 datasets · **Closes:** [#12](https://github.com/cecimerelo/ml-sandbox/issues/12) · **Answers:** [#16](https://github.com/cecimerelo/ml-sandbox/issues/16)

> **Partly superseded by F-003.** The regret advantage below did not survive doubling the
> collection. Kept as written, because a findings log that quietly edits its earlier
> numbers cannot be checked against anything.

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

---

## F-002 — The tie is a real tie, and the regime pattern does not survive testing

**Date:** 2026-08-31 · **Run:** `results-801f29e62585.parquet`, 60 datasets · **Follows:** F-001

> **Superseded by F-003.** The limitation this recorded was resolved by growing the
> collection: the pattern is gone at double the sample.

F-001 left open whether Layer 2's tie with the fixed baseline hides a regime where it wins.
It was worth asking and the answer is no — with a qualification worth stating precisely.

### The tie is not an average hiding a pattern

On the 29 datasets where the choice makes a difference, the two disagree eight times and
**split them exactly four and four**. Nine times both are right, twelve times neither is.

### There is a pattern, and it is interpretable

| Regime | n | Layer 2 | Baseline |
|---|---|---|---|
| 500–10k rows | 9 | **0.78** | 0.44 |
| under 10 columns | 13 | **0.62** | 0.38 |
| over 10k rows | 12 | 0.33 | **0.58** |
| under 500 rows | 8 | 0.25 | 0.25 |

It reads sensibly: on large data-rich problems boosting wins almost regardless, so there is
nothing to personalise; on medium problems with few predictors the best method genuinely
varies and a model can learn which.

### It does not hold up

| Comparison | p |
|---|---|
| Hits in the 500–10k band (3–0 to Layer 2) | 0.250 |
| Regret across all discriminating datasets | 0.332 |
| Regret in the 500–10k band (0.026 against 0.052) | **0.109** |

The band is **nine datasets and they disagree on three**. Three in a row favouring one side
happens by chance one time in four — the same odds as three coin flips.

**Reported as a limitation, not as a finding.** *"Layer 2 wins on medium datasets"* is the
first claim that would fall apart under questioning, and it would deserve to.

What can be said: **the advantage is not uniform.** It concentrates where the data is
medium-sized and narrow, halving regret there — and this study lacks the power to establish
that.

**What would settle it: more datasets between 500 and 10,000 rows.** Not more methods, not
more folds, and specifically **not more large datasets** — above ten thousand rows the two
strategies already agree, because boosting wins almost regardless and there is nothing left
to personalise. Adding large datasets would confirm something already confirmed. The
unresolved question lives entirely in the middle band, where nine datasets disagreeing on
three cannot tell a signal from three coin flips, and thirty could.

---

---

## F-003 — At double the sample, there is no difference to find

**Date:** 2026-09-03 · **Run:** `results-801f29e62585.parquet`, **106 datasets, complete** · **Supersedes:** F-001, F-002

> **Partly superseded by F-004.** Ridge was re-run with a wider alpha grid after this was
> written, which moved several figures by up to 0.02 — and the fixed baseline below is Random
> Forest, not Gradient Boosting, in this run as well as the later one. The conclusions stand.

38,820 evaluations. 965 unscored (2.5%): QDA on singular covariances, Lasso timing out
under `saga`, the 120 refusals `polynomial_interactions` was predicted to produce (D-046),
and 28 Ridge timeouts.

*An earlier version of this entry was computed one dataset short and said so. Regenerated
on the complete run; nothing moved by more than 0.02.*

The collection was grown from 60 to 106 because F-002 could not resolve whether Layer 2's
tie with the fixed baseline hid a regime where it won. It resolved it, and it also
**overturned part of F-001.**

The discriminating stratum nearly doubled — 29 datasets to 51 — and grew in proportion to
the collection, so the datasets added were no easier than the ones already there.

### Where the choice makes a difference (51 datasets)

| Strategy | Hit | Top-3 | Regret |
|---|---|---|---|
| Single best method | **0.47** | 0.65 | **0.031** |
| Learned (Layer 2) | **0.47** | **0.69** | 0.039 |
| Heuristics (ISLR) | 0.18 | 0.49 | 0.112 |
| Random choice | 0.02 | 0.29 | 0.325 |

Across all 106 the hit rates tie too — 0.62 each.

### Nothing separates the two, on any metric

| Comparison | Result | p |
|---|---|---|
| Hit rate | 4 wins each | **1.000** |
| Top-3 | 3 to 1 for Layer 2 | 0.625 |
| Regret | 0.039 against 0.031 | 0.768 |
| The 500–10k band | 2 wins each | **1.000** |

## What this corrects

**F-001's 26% regret advantage was noise.** At 29 datasets Layer 2 gave up 0.028 against
the baseline's 0.038, and it was reported as the finding that saved the model from looking
worthless. At 51 it is 0.040 against 0.032 — **reversed**, and not significant either way.

**F-002's regime pattern does not exist.** The 3–0 in the 500–10k band, recorded as a
limitation the study lacked power to settle, is now **2–2**. There was nothing to settle.

## What this establishes

The tie moves from *"we cannot tell"* to *"there is no difference we can detect at double
the sample"*. That is a stronger claim and a more defensible one: at 29 datasets the result
was underpowered, and 4 wins each at p = 1.000 across 51 is a well-supported null.

**Inspecting the user's problem does not beat always recommending Gradient Boosting.** Not
in how often it is right, not in how much it gives up when it is wrong. The hit rates are
identical to two decimal places in both strata.

### One direction has never reversed

Layer 2 is ahead on **top-3** in all three runs — 0.77 against 0.75 at 60 datasets, 0.70
against 0.66 at 105, 0.69 against 0.65 at 106. It is the only comparison that has not
flipped, and it is **not significant** (3 wins to 1, p = 0.625).

Worth stating as a hypothesis rather than a result, and worth stating because it matches
what the interface does: it shows three alternatives, not one. *Personalising may not help
you pick the winner, but it may help you put the winner on the shortlist.* Establishing
that needs more datasets than this study has — and unlike F-002's regime pattern, this one
has survived every enlargement so far rather than dissolving under one.

## What the ISLR result does not say

The heuristics lose as a **selection procedure**. That is the whole of the claim, and the
distance between it and *"the textbook is not pedagogical"* is where this study would be
attacked if it overreached.

**They carry real signal.** 0.18 against random's 0.02 — nine times better than choosing
blind. They are not noise; they are beaten.

**What beats them is not a teachable alternative.** *"Always use Gradient Boosting"* is a
fact about modern tabular data, not an understanding anyone could be taught. There is no
chapter to write about it, and a student who learned it would know one thing rather than a
subject.

**And the book does not promise this.** It promises that a reader understands *why* methods
behave as they do — the bias-variance trade-off, what regularisation buys, when interactions
matter. Someone who has read it can read a residual plot, diagnose overfitting, and explain
a coefficient. **This benchmark measures none of that**, and cannot.

## The result is about the problem, not the book

If a fixed choice matches reasoned selection, that is a statement about how much method
choice matters on typical tabular data: **less than the field assumes.** ISLR does not tell
a reader that, and this study found it. Read that way it is a positive result wearing a
negative one's clothes — and it is the reading the evidence actually supports.

## What still holds, with more margin than before

**ISLR's heuristics are clearly beaten** — 0.18 against 0.48, and the gap widened from
F-001's 0.24 against 0.45. Still far above chance (0.02), so they carry real signal, and
comfortably behind a single fixed choice.

**Requiring explainability costs about 0.11 regret and binds on 103 of 106 datasets.** The
best available method is almost always an opaque one.

## Why growing the collection was worth the compute

It cost about eight hours and it changed three things: a consoling result was shown to be
noise, an open question was closed, and an underpowered tie became an established one.

Had the collection been grown **only** in the band where the result was unresolved, the
same numbers would carry none of that weight — they would describe a sample shaped around
the answer we were hoping for. Growing every stratum equally is what makes this a
measurement rather than a search.

---

## F-004 — After the Ridge re-run: the same answer, and the questions F-003 left open

**Date:** 2026-09-27 · **Run:** `results-801f29e62585.parquet`, 106 datasets, after Ridge's
alpha grid was widened (2026-09-20) · **Supersedes in part:** F-003

38,820 evaluations. 954 unscored (2.5%): 667 QDA errors on singular covariances, 150 Lasso
timeouts, the 120 `polynomial_interactions` refusals (D-046) and 17 Ridge timeouts, down from
28 now that Ridge has more alphas to choose from.

### What changed, and what did not

RidgeCV used scikit-learn's default of three alphas (0.1, 1, 10). It now searches 25, from
0.001 to 1,000, and only Ridge was re-run. It improved on 10 of the 106 datasets — by 0.22 on
one, by little on the rest. Because a hit means choosing a method the tie rule counts among the
best, a better Ridge changes who counts as best on a handful of datasets, and the strategies'
figures move with it.

**The evaluation itself did not change.** Re-running it on the pre-fix copy of the parquet
(`.before-ridge-alphas-widen`) reproduces every F-003 figure to the third decimal. The
per-dataset outcomes are now exported (`scripts/export_outcomes.py` →
`data/results/outcomes.parquet`, `method_scores.parquet`, `explainability.json`) and drive the
thesis notebook, `notebooks/tfm_graficos.ipynb`.

### Where the choice makes a difference (51 datasets)

| Strategy | Hit | 95% CI | Top-3 | 95% CI | Regret |
|---|---|---|---|---|---|
| Learned (Layer 2) | **0.49** | 0.35–0.63 | **0.69** | 0.55–0.80 | 0.038 |
| Single best method | 0.47 | 0.33–0.61 | 0.65 | 0.51–0.78 | **0.031** |
| Heuristics (ISLR) | 0.18 | 0.08–0.29 | 0.49 | 0.35–0.63 | 0.112 |
| Random choice | 0.02 | 0.00–0.06 | 0.29 | 0.18–0.43 | 0.325 |

Bootstrap intervals over datasets, 2,000 resamples. Across all 106: hit 0.63 against 0.62.
The interval F-003 asked for is now there, and it is wide — fourteen points either side — which
is the honest size of what 51 datasets can resolve.

### The tie holds, on every cut

| Learned against fixed | 106 datasets | 51 datasets |
|---|---|---|
| Hit rate (McNemar exact) | 7 to 6, p = 1.000 | 4 to 3, p = 1.000 |
| Top-3 | 5 to 1, p = 0.219 | 3 to 1, p = 0.625 |
| Regret (Wilcoxon) | 21 to 19, p = 0.485 | 11 to 9, p = 0.546 |
| The 500–10k band | | 2 to 2, p = 1.000 |

The learned strategy's **worst** miss is larger than the baseline's — a regret of 0.50 against
0.28 — which is why its mean regret is higher while its hit rate is not.

### The fixed baseline is Random Forest

F-003 says *"always recommending Gradient Boosting"*. That came from the first 60-dataset
pass and was already wrong for the complete run: the single-best strategy picks **Random
Forest on all 106 held-out datasets**, before the Ridge fix and after it. Under the tie rule
Random Forest is among the best on 66 datasets, Gradient Boosting on 62. The finding is
unchanged — a fixed choice matches reasoned selection — but the name was not.

It ranks by lowest mean shortfall from the best, not by how often a method wins. Here both
criteria name the same method, so nothing turns on it, but it is what the code does.

### The ISLR result, tested rather than eyeballed

F-003 set heuristics against random by their point estimates. Paired:

| Heuristics against random | 106 datasets | 51 datasets |
|---|---|---|
| Hit rate | 21 to 15, p = 0.41 | **9 to 1, p = 0.02** |
| Top-3 | 22 to 13, p = 0.18 | 16 to 6, p = 0.053 |
| Regret | **62 to 43, p = 0.002** | **36 to 15, p = 0.001** |

They lose less than random everywhere, but pick the winner more often **only where the choice
matters**; across all 106, random's hits from ties close the gap. Against the fixed baseline
they lose on hit rate and regret in both strata (p < 0.001). *"They carry real signal"* holds;
*"nine times better than choosing blind"* holds only on the narrowed stratum.

### Missing data, finally looked at

| Hit rate, all 106 | 0% | 5% | 25% |
|---|---|---|---|
| Learned (Layer 2) | 0.63 | 0.73 | 0.69 |
| Single best method | 0.62 | 0.76 | 0.69 |
| Heuristics (ISLR) | 0.32 | 0.30 | 0.29 |
| Random choice | 0.26 | 0.30 | 0.27 |

No paired comparison of learned against fixed is significant at either rate (all p ≥ 0.45). The
tie survives incomplete data; at 5% the baseline is nominally ahead. Two caveats bound it: the
gaps are MCAR, the most benign pattern, and **Layer 2 trains on the 0% results at every rate**
while the fixed baseline's ordering pools all three — an asymmetry that favours the baseline,
not one that could manufacture the tie.

### Explainability: the constraint is cheap, the recommender is not

F-003 read the hybrid's regret under a constraint as *the cost of explainability* — about 0.11.
It is not. That figure mixes two things, and separating them changes the finding.

| Level | Best allowed method's regret (unavoidable) | Hybrid's regret |
|---|---|---|
| `not important` | 0.000 | 0.041 |
| `somewhat` | **0.027** | 0.156 |
| `critical` | **0.061** | 0.146 |

The unavoidable cost — how far the best permitted method sits below the best overall — is
small and rises with strictness, as it should. The constraint still binds on 103 of 106
datasets, because the best method is almost always opaque; it simply does not cost much.

**Most of the hybrid's loss is Layer 2 choosing badly among the permitted methods**, two to six
times the unavoidable cost. At `somewhat` it picks KNN 42 times and QDA or
`polynomial_interactions` often enough that 4.7% of its picks never ran and are charged in
full; at `critical` it picks the decision tree 71 times. That is why the stricter level looked
*cheaper*: fewer options, fewer ways to choose wrong.

Layer 2 learned to order the strong methods, where the training signal is — they are the ones
that win — and not the simple ones. It is the clearest improvement available to the
recommender.

### Not done

The packaged model the application serves (`data/model/layer2.joblib`, 2026-09-05) predates
the Ridge fix; the Ridge commit called for re-running `scripts/package_model.py` and that has
not happened. It affects what the application recommends, not any figure above, which all come
from the leave-one-dataset-out evaluation.

---

## Not yet established

**How stable the 29-dataset stratum is.** Small enough to want an interval rather than a
point estimate. An earlier partial run put the same comparison 15 points elsewhere.
*Addressed in F-004: bootstrap intervals on the 51-dataset stratum, about fourteen points
either side.*

**Anything about missing data.** Every figure up to F-003 is at 0% missingness. *Addressed
in F-004: the tie holds at 5% and 25%.*
