"""Comparing the strategies — and the ways that comparison can quietly stop being fair."""

import pandas as pd
import pytest

from mlsandbox.baselines import DatasetScores, summarise
from mlsandbox.evaluation import TOP_K, discriminating, evaluate
from mlsandbox.metafeatures import MetaFeatures

FEATURES = dict(
    task="binary classification",
    rows="500-10k",
    features="10-50",
    regime="moderate",
    feature_types="numeric",
    missing="none",
    class_balance="roughly equal",
)


def result(dataset: str, method: str, score: float, fold: int = 0) -> dict:
    return {
        "dataset": dataset,
        "method": method,
        "score": score,
        "status": "ok",
        "missing_rate": 0.0,
        "fold": fold,
    }


@pytest.fixture
def collection() -> tuple[pd.DataFrame, pd.DataFrame]:
    """Six datasets where random_forest is reliably best, with fold-level spread."""
    rows = []
    for i in range(6):
        for fold in range(3):
            rows.append(result(f"d{i}", "random_forest", 0.90 + 0.001 * fold, fold))
            rows.append(result(f"d{i}", "logistic_regression", 0.60 + 0.001 * fold, fold))
            rows.append(result(f"d{i}", "knn", 0.50 + 0.001 * fold, fold))
            rows.append(result(f"d{i}", "decision_tree", 0.40 + 0.001 * fold, fold))
    results = pd.DataFrame(rows)
    metafeatures = pd.DataFrame(
        [{"dataset": f"d{i}", **FEATURES} for i in range(6)]
    )
    return results, metafeatures


def test_every_strategy_is_scored_on_the_same_datasets(collection):
    """Different denominators would make the rates incomparable without looking wrong."""
    scores = evaluate(*collection, seed=0)
    assert len({score.datasets for score in scores}) == 1


def test_all_five_strategies_are_reported(collection):
    from mlsandbox.strategies import STRATEGIES

    assert {score.strategy for score in evaluate(*collection, seed=0)} == set(STRATEGIES)


def test_rates_stay_within_bounds(collection):
    for score in evaluate(*collection, seed=0):
        assert 0.0 <= score.hit_rate <= 1.0
        assert score.hit_rate <= score.top_k_hit_rate
        assert score.mean_regret >= 0.0


def test_a_dataset_where_everything_ties_is_not_discriminating():
    summary = DatasetScores(
        dataset="d",
        scores={f"m{i}": 0.5 for i in range(6)},
        best_score=0.5,
        winners=[f"m{i}" for i in range(6)],
    )
    assert not discriminating(summary)


def test_a_dataset_with_one_clear_winner_is_discriminating():
    summary = DatasetScores(
        dataset="d",
        scores={"a": 0.9, "b": 0.2},
        best_score=0.9,
        winners=["a"],
    )
    assert discriminating(summary)


def test_the_threshold_is_what_the_interface_shows():
    """Not a number chosen to move the results.

    Where more than TOP_K methods are best, a user following the tool's three suggestions
    cannot land wrong — there is nothing there for a strategy to get right.
    """
    at_limit = DatasetScores(
        dataset="d",
        scores={f"m{i}": 0.5 for i in range(TOP_K + 1)},
        best_score=0.5,
        winners=[f"m{i}" for i in range(TOP_K)],
    )
    assert discriminating(at_limit)


def test_narrowing_the_stratum_does_not_narrow_the_training(collection):
    """Scoring on the hard datasets is the point; training only on them is not.

    A deployed recommender learns from every dataset it has, easy ones included, so
    removing them from training would measure a system nobody would build.
    """
    results, metafeatures = collection
    narrowed = evaluate(results, metafeatures, seed=0, only_discriminating=True)
    assert all(score.stratum == "discriminating" for score in narrowed)


def test_the_stratum_is_recorded_on_the_score(collection):
    """So a table cannot be captioned as the wrong one."""
    assert all(s.stratum == "all" for s in evaluate(*collection, seed=0))


def test_summarise_and_evaluate_agree_on_which_datasets_exist(collection):
    results, metafeatures = collection
    assert {s.dataset for s in summarise(results)} == set(metafeatures.dataset)


def test_metafeatures_round_trip_through_the_table(collection):
    """The evaluation rebuilds MetaFeatures from the exported table, so the columns have
    to still line up with the model."""
    _, metafeatures = collection
    row = metafeatures.iloc[0]
    assert MetaFeatures(**{f: row[f] for f in MetaFeatures.model_fields})
