"""The five ways of choosing a method, behind one interface.

The thesis compares them, so they have to be comparable: same candidates, same ranked
output, same ignorance of the dataset being judged. Anything a strategy learns, it learns
from other datasets — which is why they are built from a training split rather than
configured once and reused.

The interface is a ranking rather than a single choice on purpose. The interface shows
alternatives (FR-2.2), so measuring only the top method would measure something the user
does not see.
"""

from __future__ import annotations

from collections.abc import Callable

import numpy as np
import pandas as pd

from mlsandbox import layer1, layer2
from mlsandbox.base import StrictModel
from mlsandbox.metafeatures import MetaFeatures

Ranker = Callable[[MetaFeatures, list[str]], list[str]]
"""Order these candidate methods for this problem, best first."""


class Split(StrictModel):
    """What a strategy is allowed to learn from.

    Results and meta-features for the training datasets only. A strategy that peeked at
    the dataset it is about to be judged on would report a number no deployed system could
    reproduce — and it would not fail, it would simply look good.
    """

    results: object
    metafeatures: object

    model_config = {"arbitrary_types_allowed": True, "frozen": True}


def random_choice(split: Split, *, seed: int) -> Ranker:
    """Shuffle. The floor: what you get without looking at anything."""
    rng = np.random.default_rng(seed)

    def rank(features: MetaFeatures, candidates: list[str]) -> list[str]:
        order = sorted(candidates)
        rng.shuffle(order)
        return order

    return rank


def single_best(split: Split, *, seed: int) -> Ranker:
    """Always the method that won most often on the training datasets.

    The comparison that decides whether the thesis has a contribution: not *"better than
    guessing?"* but *"is there any point looking at the user's problem at all?"* (D-031).

    Learned from the training split rather than from everything. Choosing the overall
    winner across all sixty datasets — the held-out one included — hands the baseline
    information no deployed recommender could have. It does not error; it just makes the
    bar to beat quietly higher than it should be, biasing the study toward the conclusion
    that the recommender adds nothing.
    """
    frame = split.results
    scored = frame[frame.status == "ok"]
    if scored.empty:
        return lambda features, candidates: sorted(candidates)

    means = scored.groupby(["dataset", "method"])["score"].mean().reset_index()
    best = means.groupby("dataset")["score"].transform("max")
    # Rank by how often a method is the best available, then by how close it stays when it
    # is not — a method that wins rarely but never trails badly is the safer fixed choice.
    means["shortfall"] = best - means["score"]
    order = (
        means.groupby("method")["shortfall"]
        .mean()
        .sort_values()
        .index.tolist()
    )

    def rank(features: MetaFeatures, candidates: list[str]) -> list[str]:
        ranked = [method for method in order if method in candidates]
        return ranked + sorted(set(candidates) - set(ranked))

    return rank


def heuristics(
    split: Split,
    *,
    seed: int,
    explainability: layer1.Explainability = "not important",
    suspects_non_linearity: layer1.Suspicion = "no",
    suspects_interactions: layer1.Suspicion = "no",
) -> Ranker:
    """What the textbook says. Learns nothing — that is the point.

    ISLR's advice does not change with evidence, so `split` is ignored. It is accepted
    anyway so every strategy is built the same way and none can quietly be given more than
    the others.
    """

    def rank(features: MetaFeatures, candidates: list[str]) -> list[str]:
        recommendations = layer1.recommend(
            features,
            candidates,
            explainability=explainability,
            suspects_non_linearity=suspects_non_linearity,
            suspects_interactions=suspects_interactions,
        )
        return [r.method for r in recommendations]

    return rank


def learned(split: Split, *, seed: int) -> Ranker:
    """Layer 2: fit on the training datasets, rank by predicted shortfall.

    Falls back to alphabetical order when the split holds too little to fit on, rather
    than raising. A fold that cannot train is a result about data volume, and crashing
    would lose every other fold's answer with it.
    """
    if split.results.empty:
        return lambda features, candidates: sorted(candidates)

    table = layer2.build_training_table(split.results, split.metafeatures)
    if len(np.asarray(table.target)) == 0:
        return lambda features, candidates: sorted(candidates)

    model = layer2.build_model(seed)
    model.fit(table.frame, table.target)

    def rank(features: MetaFeatures, candidates: list[str]) -> list[str]:
        return [p.method for p in layer2.rank_methods(model, features, candidates)]

    return rank


def hybrid(
    split: Split,
    *,
    seed: int,
    explainability: layer1.Explainability = "not important",
    suspects_non_linearity: layer1.Suspicion = "no",
    suspects_interactions: layer1.Suspicion = "no",
) -> Ranker:
    """The user's constraints filter; the evidence orders what survives.

    Two kinds of statement, kept apart. A heuristic says *"this usually fits badly"* and
    evidence should be able to overturn it — so the heuristics do not vote on the ordering
    here, where a model trained on real results is better placed to judge. A constraint
    says *"I cannot use this"*, and no accuracy makes an unexplainable model usable where
    the decision has to be defended. Blended into a single score, a large enough predicted
    advantage would overrule a requirement the user stated (D-035).

    Identical to `learned` when the user has no constraints, which is the honest outcome:
    with nothing to filter, filtering adds nothing.
    """
    rank_by_evidence = learned(split, seed=seed)

    def rank(features: MetaFeatures, candidates: list[str]) -> list[str]:
        blocked = set(
            layer1.excluded_by_constraints(candidates, explainability=explainability)
        )
        allowed = [method for method in candidates if method not in blocked]
        if not allowed:
            # Every method ruled out. Ordering the excluded ones is more useful than
            # returning nothing: the interface can then show what the constraint cost.
            return rank_by_evidence(features, candidates)
        return rank_by_evidence(features, allowed) + [
            method for method in rank_by_evidence(features, candidates) if method in blocked
        ]

    return rank


STRATEGIES: dict[str, Callable[..., Ranker]] = {
    "random choice": random_choice,
    "single best method": single_best,
    "heuristics (ISLR)": heuristics,
    "learned (Layer 2)": learned,
    "hybrid": hybrid,
}
"""Every strategy the study compares, built the same way so none is privileged."""


def build_split(results: pd.DataFrame, metafeatures: pd.DataFrame, datasets: set[str]) -> Split:
    """Restrict both tables to the named datasets."""
    return Split(
        results=results[results.dataset.isin(datasets)],
        metafeatures=metafeatures[metafeatures.dataset.isin(datasets)],
    )
