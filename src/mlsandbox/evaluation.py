"""Comparing the strategies on the same ground.

The number this module produces is the thesis's answer, so the way it is produced matters
more than the number. Two things it enforces:

**Nothing is judged on a dataset it learned from.** Every strategy is rebuilt for each
held-out dataset from the other fifty-nine. Not because all of them learn — the heuristics
do not — but because a comparison where one side trains on the test set and another does
not is not measuring what it appears to.

**Every strategy faces the same candidates and the same scoring.** Same tie rule, same
treatment of methods that failed to run. Where those differ between strategies, the
resulting number still looks perfectly reasonable, which is what makes it dangerous.
"""

from __future__ import annotations

import pandas as pd

from mlsandbox import strategies
from mlsandbox.base import StrictModel
from mlsandbox.baselines import DatasetScores, summarise
from mlsandbox.metafeatures import MetaFeatures
from mlsandbox.methods import available

TOP_K = 3
"""The interface shows a recommendation and its alternatives, so the study reports whether
the best method appears anywhere a user would look — not only in first place."""


def discriminating(summary: DatasetScores) -> bool:
    """Whether choosing a method on this dataset makes any difference.

    On average five of the fourteen methods that run tie with the best, and on some
    datasets every single one does — on `schizo`, all fourteen. Those datasets hand a hit
    to every strategy alike, and pooled over the collection they dominate: with roughly a
    third of methods tying, three drawn at random contain a winner 77% of the time, which
    is exactly the top-3 rate random choice achieves. The metric was largely measuring how
    often the question has no wrong answer.

    Reported as a separate stratum rather than replacing the pooled figure, because both
    are true and they answer different questions: *"how often does the recommendation
    matter?"* and *"when it matters, does the recommender get it right?"*

    The threshold is `TOP_K`, not a number picked to make the numbers move. The interface
    shows three alternatives, so where more than three methods are best, a user following
    the tool cannot land wrong — there is nothing there for a strategy to get right.
    """
    return len(summary.winners) <= TOP_K


class StrategyScore(StrictModel):
    """How one strategy did across the collection."""

    strategy: str
    hit_rate: float
    """Share of datasets where its first choice was among the best (D-031's tie rule)."""

    top_k_hit_rate: float
    """Share where the best method appeared in the first `TOP_K` — what the user sees."""

    mean_regret: float
    """Average performance given up by following the first choice. Reported alongside the
    hit rate because they answer differently: a strategy can rarely pick the winner and
    still always land close, which is a good recommender by any use a person has for one."""

    datasets: int
    stratum: str = "all"
    """`all`, or `discriminating` for the datasets where the choice makes a difference."""


class ConstraintCost(StrictModel):
    """What requiring explainability costs, in the study's metric.

    Reported rather than hidden. Filtering out the best method is what a constraint *means*
    — but doing it silently leaves the user unable to weigh the trade, so the size of the
    trade is measured (D-035).
    """

    explainability: str
    mean_regret: float
    unconstrained_mean_regret: float
    datasets_where_it_bound: int
    """How often the constraint actually removed the method that would have been chosen.
    Where it never binds, the cost is zero and the comparison says nothing."""

    @property
    def cost(self) -> float:
        return self.mean_regret - self.unconstrained_mean_regret


def _candidates(task: str, summary: DatasetScores) -> list[str]:
    """The methods a user could choose for this problem.

    Every method that applies to the task, not merely the ones that ran. A method that
    errored is still one the user could have picked, and a recommender that suggests it has
    given advice that cannot be followed — which the scoring below charges for. Restricting
    candidates to what succeeded would hand every strategy a free pass on recommending
    something broken.
    """
    return sorted(m.name for m in available(task))


def _regret(summary: DatasetScores, method: str) -> float:
    """What choosing this method cost, with a failed method charged in full.

    A recommendation that does not run is worth nothing to the user, so it gives up the
    whole of the best available score rather than being quietly skipped.
    """
    value = summary.regret(method)
    return summary.best_score if value is None else value


def evaluate(
    results: pd.DataFrame,
    metafeatures: pd.DataFrame,
    *,
    seed: int,
    missing_rate: float = 0.0,
    strategy_options: dict | None = None,
    only_discriminating: bool = False,
) -> list[StrategyScore]:
    """Score every strategy, holding out one dataset at a time.

    `only_discriminating` narrows the *scoring* to datasets where the choice matters. It
    does not narrow what the strategies train on: a recommender deployed in the world
    learns from every dataset it has, including the easy ones, so removing them from
    training would measure a system nobody would build.
    """
    summaries = {s.dataset: s for s in summarise(results, missing_rate=missing_rate)}
    tasks = dict(zip(metafeatures.dataset, metafeatures.task, strict=True))
    all_datasets = set(summaries) & set(tasks)
    scored_datasets = (
        {name for name in all_datasets if discriminating(summaries[name])}
        if only_discriminating
        else all_datasets
    )
    options = strategy_options or {}

    tallies: dict[str, list[tuple[bool, bool, float]]] = {
        name: [] for name in strategies.STRATEGIES
    }

    for held_out in sorted(scored_datasets):
        summary = summaries[held_out]
        features = _features_for(metafeatures, held_out)
        task = "regression" if features.task == "regression" else "classification"
        candidates = _candidates(task, summary)
        split = strategies.build_split(results, metafeatures, all_datasets - {held_out})

        for name, factory in strategies.STRATEGIES.items():
            ranker = factory(split, seed=seed, **options.get(name, {}))
            ranked = ranker(features, candidates)
            if not ranked:
                continue
            tallies[name].append(
                (
                    summary.is_hit(ranked[0]),
                    any(summary.is_hit(method) for method in ranked[:TOP_K]),
                    _regret(summary, ranked[0]),
                )
            )

    return [
        StrategyScore(
            strategy=name,
            hit_rate=sum(hit for hit, _, _ in rows) / len(rows),
            top_k_hit_rate=sum(top for _, top, _ in rows) / len(rows),
            mean_regret=sum(regret for _, _, regret in rows) / len(rows),
            datasets=len(rows),
            stratum="discriminating" if only_discriminating else "all",
        )
        for name, rows in tallies.items()
        if rows
    ]


def cost_of_explainability(
    results: pd.DataFrame,
    metafeatures: pd.DataFrame,
    *,
    seed: int,
    level: str = "critical",
    missing_rate: float = 0.0,
) -> ConstraintCost:
    """How much performance a user gives up by requiring explainable models.

    The unconstrained hybrid is the reference: same strategy, same folds, constraint off.
    Anything else would confound the cost of the constraint with the difference between
    two strategies.
    """
    from mlsandbox import layer1

    summaries = {s.dataset: s for s in summarise(results, missing_rate=missing_rate)}
    all_datasets = set(summaries) & set(metafeatures.dataset)

    constrained, unconstrained, bound = [], [], 0
    for held_out in sorted(all_datasets):
        summary = summaries[held_out]
        features = _features_for(metafeatures, held_out)
        task = "regression" if features.task == "regression" else "classification"
        candidates = _candidates(task, summary)
        split = strategies.build_split(results, metafeatures, all_datasets - {held_out})

        free = strategies.hybrid(split, seed=seed)(features, candidates)
        held = strategies.hybrid(split, seed=seed, explainability=level)(features, candidates)
        if not free or not held:
            continue

        constrained.append(_regret(summary, held[0]))
        unconstrained.append(_regret(summary, free[0]))
        blocked = layer1.excluded_by_constraints(candidates, explainability=level)
        bound += free[0] in blocked

    return ConstraintCost(
        explainability=level,
        mean_regret=sum(constrained) / len(constrained),
        unconstrained_mean_regret=sum(unconstrained) / len(unconstrained),
        datasets_where_it_bound=bound,
    )


def _features_for(metafeatures: pd.DataFrame, dataset: str) -> MetaFeatures:
    row = metafeatures[metafeatures.dataset == dataset].iloc[0]
    return MetaFeatures(
        **{
            field: row[field]
            for field in MetaFeatures.model_fields
        }
    )
