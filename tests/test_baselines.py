"""What the recommender has to beat.

The failure these guard against is a baseline that flatters the recommender — by scoring a
method's failure as zero, by picking a different tie rule, or by counting an
unfollowable recommendation as free.
"""

import pandas as pd
import pytest

from mlsandbox.baselines import (
    random_baseline,
    single_best_baseline,
    summarise,
)


def results(rows: list[dict]) -> pd.DataFrame:
    return pd.DataFrame(
        [{"status": "ok", "missing_rate": 0.0, "fold": i, **row} for i, row in enumerate(rows)]
    )


def folds_of(dataset: str, method: str, scores: list[float]) -> list[dict]:
    return [{"dataset": dataset, "method": method, "score": s} for s in scores]


@pytest.fixture
def two_datasets() -> pd.DataFrame:
    return results(
        folds_of("A", "linear", [0.60, 0.60])
        + folds_of("A", "forest", [0.80, 0.80])
        + folds_of("B", "linear", [0.75, 0.75])
        + folds_of("B", "forest", [0.72, 0.72])
    )


def test_the_best_method_per_dataset_is_identified(two_datasets):
    by_name = {s.dataset: s for s in summarise(two_datasets)}
    assert by_name["A"].winners == ["forest"]
    assert by_name["B"].winners == ["linear"]


def test_methods_within_one_standard_deviation_all_count_as_best():
    # With fifteen methods, several are usually indistinguishable. Naming a single winner
    # would exaggerate how hard the choice is, and inflate every strategy's apparent error.
    close = results(
        folds_of("A", "one", [0.70, 0.90])  # mean 0.80, sd 0.14
        + folds_of("A", "two", [0.72, 0.72])
    )
    assert summarise(close)[0].winners == ["one", "two"]


def test_a_method_that_never_ran_is_absent_not_zero(two_datasets):
    # Absent and zero are different claims, and conflating them would let any strategy
    # that avoided a failing method look better than it was.
    summary = summarise(two_datasets)[0]
    assert summary.regret("qda") is None
    assert "qda" not in summary.scores


def test_failed_folds_do_not_contribute_a_score():
    frame = results(folds_of("A", "linear", [0.9]) + folds_of("A", "qda", [0.0]))
    frame.loc[frame.method == "qda", "status"] = "error"
    assert "qda" not in summarise(frame)[0].scores


def test_regret_is_the_gap_to_the_best(two_datasets):
    summary = {s.dataset: s for s in summarise(two_datasets)}["A"]
    assert summary.regret("linear") == pytest.approx(0.20)
    assert summary.regret("forest") == pytest.approx(0.0)


def test_random_never_picks_a_method_that_failed():
    # Scoring failures as zero would make random look worse and the recommender better by
    # comparison — and a user who saw an error would try something else, not give up.
    frame = results(folds_of("A", "good", [0.8]) + folds_of("A", "qda", [0.0]))
    frame.loc[frame.method == "qda", "status"] = "error"

    result = random_baseline(summarise(frame), seed=1, repetitions=50)

    assert result.hit_rate == 1.0  # only `good` was ever available
    assert result.mean_regret == 0.0


def test_random_is_reported_with_an_interval(two_datasets):
    # One draw is an accident of the seed.
    result = random_baseline(summarise(two_datasets), seed=1, repetitions=200)
    low, high = result.hit_rate_interval
    assert low <= result.hit_rate <= high


def test_random_lands_between_the_worst_and_best_choices(two_datasets):
    result = random_baseline(summarise(two_datasets), seed=1, repetitions=500)
    assert 0.0 < result.hit_rate < 1.0


def test_random_is_reproducible(two_datasets):
    summaries = summarise(two_datasets)
    first = random_baseline(summaries, seed=7, repetitions=100)
    second = random_baseline(summaries, seed=7, repetitions=100)
    assert first.hit_rate == second.hit_rate


def test_the_single_best_method_is_the_one_winning_most_often():
    frame = results(
        folds_of("A", "forest", [0.9]) + folds_of("A", "linear", [0.5])
        + folds_of("B", "forest", [0.9]) + folds_of("B", "linear", [0.5])
        + folds_of("C", "forest", [0.5]) + folds_of("C", "linear", [0.9])
    )
    result = single_best_baseline(summarise(frame))
    assert "forest" in result.detail
    assert result.hit_rate == pytest.approx(2 / 3)


def test_a_fixed_method_that_could_not_run_costs_its_full_regret():
    # A recommendation the user cannot follow is worth nothing to them, so it cannot be
    # scored as if no choice had been made.
    frame = results(
        folds_of("A", "forest", [0.9]) + folds_of("B", "forest", [0.9])
        + folds_of("C", "linear", [0.6])
    )
    result = single_best_baseline(summarise(frame))
    assert "forest" in result.detail
    assert result.mean_regret == pytest.approx(0.6 / 3)


def test_the_single_best_baseline_is_deterministic():
    # No seed, and no tie-breaking by dictionary order: two runs must agree.
    frame = results(
        folds_of("A", "alpha", [0.9]) + folds_of("A", "beta", [0.9])
        + folds_of("B", "alpha", [0.9]) + folds_of("B", "beta", [0.9])
    )
    summaries = summarise(frame)
    assert single_best_baseline(summaries).detail == single_best_baseline(summaries).detail
