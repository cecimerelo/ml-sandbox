"""The five strategies, and what keeps them comparable."""

import pandas as pd
import pytest

from mlsandbox import strategies
from mlsandbox.metafeatures import MetaFeatures

CANDIDATES = ["logistic_regression", "decision_tree", "random_forest", "knn", "mlp"]


def problem(**overrides) -> MetaFeatures:
    defaults = dict(
        task="binary classification",
        rows="500-10k",
        features="10-50",
        regime="moderate",
        feature_types="numeric",
        missing="none",
        class_balance="roughly equal",
    )
    return MetaFeatures(**{**defaults, **overrides})


def split_of(rows: list[dict]) -> strategies.Split:
    results = pd.DataFrame(rows)
    metafeatures = pd.DataFrame(
        [{"dataset": name, **problem().as_row()} for name in results.dataset.unique()]
    )
    return strategies.Split(results=results, metafeatures=metafeatures)


def scored(dataset: str, method: str, score: float) -> dict:
    return {
        "dataset": dataset,
        "method": method,
        "score": score,
        "status": "ok",
        "missing_rate": 0.0,
        "fold": 0,
    }


@pytest.fixture
def split() -> strategies.Split:
    return split_of(
        [
            scored(f"d{i}", "random_forest", 0.9)
            for i in range(4)
        ]
        + [scored(f"d{i}", "logistic_regression", 0.5) for i in range(4)]
        + [scored(f"d{i}", method, 0.4) for i in range(4) for method in ("knn", "mlp")]
        + [scored(f"d{i}", "decision_tree", 0.3) for i in range(4)]
    )


@pytest.mark.parametrize("name", sorted(strategies.STRATEGIES))
def test_every_strategy_returns_every_candidate(name, split):
    """Nothing may be dropped, or the strategies are answering different questions.

    A strategy that returns four methods where another returns five is scored on a smaller
    problem, and the comparison stops being one.
    """
    ranked = strategies.STRATEGIES[name](split, seed=0)(problem(), CANDIDATES)
    assert sorted(ranked) == sorted(CANDIDATES)


@pytest.mark.parametrize("name", sorted(strategies.STRATEGIES))
def test_every_strategy_is_built_the_same_way(name, split):
    """Same signature, so none can quietly be handed more than the others."""
    assert callable(strategies.STRATEGIES[name](split, seed=0))


def test_single_best_learns_the_winner_from_the_split(split):
    ranked = strategies.single_best(split, seed=0)(problem(), CANDIDATES)
    assert ranked[0] == "random_forest"


def test_single_best_ignores_the_problem_it_is_given():
    """It is the "don't look at the user's data" baseline, so it must not."""
    split = split_of(
        [scored("d0", "random_forest", 0.9), scored("d0", "knn", 0.2)]
    )
    ranker = strategies.single_best(split, seed=0)
    small = ranker(problem(rows="<500"), CANDIDATES)
    large = ranker(problem(rows=">10k"), CANDIDATES)
    assert small == large


def test_heuristics_ignore_the_evidence(split):
    """ISLR's advice does not move with results — that is what makes it the object of
    study rather than a competitor that learns."""
    empty = strategies.Split(results=split.results.iloc[:0], metafeatures=split.metafeatures)
    assert strategies.heuristics(split, seed=0)(problem(), CANDIDATES) == strategies.heuristics(
        empty, seed=0
    )(problem(), CANDIDATES)


def test_heuristics_do_look_at_the_problem():
    ranker = strategies.heuristics(split_of([scored("d0", "knn", 0.5)]), seed=0)
    assert ranker(problem(rows="<500"), CANDIDATES) != ranker(
        problem(rows=">10k", regime="data-rich"), CANDIDATES
    )


def test_hybrid_without_constraints_is_exactly_the_learned_strategy(split):
    """The honest outcome: with nothing to filter, filtering adds nothing.

    A hybrid that differed here would be smuggling the heuristics into the ordering, where
    the study has no way to attribute the difference.
    """
    assert strategies.hybrid(split, seed=0)(problem(), CANDIDATES) == strategies.learned(
        split, seed=0
    )(problem(), CANDIDATES)


def test_hybrid_demotes_what_the_constraint_rules_out(split):
    ranked = strategies.hybrid(split, seed=0, explainability="critical")(problem(), CANDIDATES)
    assert ranked[0] != "random_forest", "an opaque method cannot be the top pick here"


def test_hybrid_still_returns_the_excluded_methods(split):
    """Ranked last, but present. The user has to be able to see what the constraint cost."""
    ranked = strategies.hybrid(split, seed=0, explainability="critical")(problem(), CANDIDATES)
    assert set(ranked) == set(CANDIDATES)
    assert ranked.index("logistic_regression") < ranked.index("random_forest")


def test_a_constraint_that_rules_out_everything_still_answers(split):
    """Better a ranked list of impossible options than nothing at all."""
    opaque_only = ["random_forest", "mlp"]
    ranked = strategies.hybrid(split, seed=0, explainability="critical")(problem(), opaque_only)
    assert sorted(ranked) == sorted(opaque_only)


def test_learned_survives_a_split_too_small_to_fit():
    """A fold that cannot train is a fact about data volume, not a reason to lose the run."""
    empty = strategies.Split(
        results=pd.DataFrame(columns=["dataset", "method", "score", "status", "missing_rate"]),
        metafeatures=pd.DataFrame(columns=["dataset"]),
    )
    assert sorted(strategies.learned(empty, seed=0)(problem(), CANDIDATES)) == sorted(CANDIDATES)


def test_build_split_restricts_both_tables(split):
    kept = strategies.build_split(split.results, split.metafeatures, {"d0", "d1"})
    assert set(kept.results.dataset) == {"d0", "d1"}
    assert set(kept.metafeatures.dataset) == {"d0", "d1"}
