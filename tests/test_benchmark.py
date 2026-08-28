"""The evaluation harness.

The timeout and the failure path are what these mostly cover. Both only run when
something has gone wrong, and a benchmark that hangs or that silently scores a crash is
worse than one that stops.
"""

import time

import numpy as np
import pandas as pd
import pytest
from sklearn.base import BaseEstimator

from mlsandbox.benchmark import R2_FLOOR, evaluate_fold, score_of, timeout_for, variants
from mlsandbox.folds import from_openml


@pytest.fixture
def data():
    rng = np.random.default_rng(0)
    features = pd.DataFrame(rng.normal(size=(40, 3)), columns=["a", "b", "c"])
    target = (rng.random(40) > 0.5).astype(int)
    return features, target


@pytest.fixture
def folds():
    return from_openml("d", [(list(range(30)), list(range(30, 40)))])


def evaluate(method, data, folds, **overrides):
    features, target = data
    kwargs = dict(
        dataset="d",
        source="pmlb",
        method=method,
        task="classification",
        features=features,
        target=target,
        folds=folds,
        fold_index=0,
        missing_rate=0.0,
        budget_seconds=30,
        seed=1,
    )
    kwargs.update(overrides)
    return evaluate_fold(**kwargs)


def test_a_successful_fold_records_a_score(data, folds):
    result = evaluate("decision_tree", data, folds)
    assert result.status == "ok"
    assert result.score is not None


def test_an_unknown_method_is_an_error_not_a_crash(data, folds):
    # A failure is a recorded outcome. One bad entry must not end a run that is hours long.
    result = evaluate("no_such_method", data, folds)
    assert result.status == "error"
    assert result.score is None


def test_a_method_that_overruns_is_cut_and_recorded(data, folds, monkeypatch):
    class Slow(BaseEstimator):
        def fit(self, _x, _y):
            time.sleep(5)
            return self

        def predict(self, x):
            return np.zeros(len(x))

    from sklearn.pipeline import Pipeline

    monkeypatch.setattr(
        "mlsandbox.benchmark.build", lambda *_a, **_k: Pipeline([("model", Slow())])
    )

    result = evaluate("decision_tree", data, folds, budget_seconds=1)

    assert result.status == "timeout"
    assert "exceeded 1s" in result.detail


def test_a_timeout_leaves_no_score(data, folds, monkeypatch):
    # Scoring a timeout as zero would rank a slow method below a bad one, which is a
    # different claim than "this did not finish".
    from sklearn.pipeline import Pipeline

    class Slow(BaseEstimator):
        def fit(self, _x, _y):
            time.sleep(5)
            return self

        def predict(self, x):
            return np.zeros(len(x))

    monkeypatch.setattr(
        "mlsandbox.benchmark.build", lambda *_a, **_k: Pipeline([("model", Slow())])
    )
    assert evaluate("decision_tree", data, folds, budget_seconds=1).score is None


def test_the_alarm_does_not_leak_into_the_next_evaluation(data, folds, monkeypatch):
    # A signal left armed would fire during an unrelated fit later in the run and be
    # recorded as that method's timeout.
    from sklearn.pipeline import Pipeline

    class Slow(BaseEstimator):
        def fit(self, _x, _y):
            time.sleep(3)
            return self

        def predict(self, x):
            return np.zeros(len(x))

    monkeypatch.setattr(
        "mlsandbox.benchmark.build", lambda *_a, **_k: Pipeline([("model", Slow())])
    )
    evaluate("decision_tree", data, folds, budget_seconds=1)
    monkeypatch.undo()

    time.sleep(1.5)
    assert evaluate("decision_tree", data, folds).status == "ok"


def test_timeouts_are_tiered_by_dataset_size():
    # A flat cap generous for 300 rows fails every ensemble on 50,000 (FR-8.4).
    assert timeout_for(300) == 60
    assert timeout_for(5_000) == 120
    assert timeout_for(50_000) == 300


def test_regression_scores_are_floored_at_zero():
    # A catastrophic model would otherwise drag an average through large negative values.
    truth = np.array([1.0, 2.0, 3.0, 4.0])
    terrible = np.array([100.0, -100.0, 100.0, -100.0])
    assert score_of("regression", truth, terrible) == R2_FLOOR


def test_classification_uses_balanced_accuracy():
    # Majority-class prediction on an imbalanced target scores 0.5, not 0.9.
    truth = np.array([0] * 9 + [1])
    majority = np.zeros(10, dtype=int)
    assert score_of("classification", truth, majority) == pytest.approx(0.5)


def test_the_unmodified_frame_is_the_baseline_variant(data):
    features, _ = data
    first_rate, first_frame = next(iter(variants(features, (0.25,), seed=1)))
    assert first_rate == 0.0
    assert first_frame.equals(features)


def test_each_requested_rate_appears_once(data):
    features, _ = data
    rates = [rate for rate, _ in variants(features, (0.25, 0.05, 0.25), seed=1)]
    assert rates == [0.0, 0.05, 0.25]


def test_expected_evaluations_uses_each_sources_fold_count():
    # OpenML's tasks define ten folds, generated ones follow the config. A single number
    # here would make the total, and the ETA built on it, wrong for most of the collection.
    from scripts.run_benchmark import expected_evaluations

    openml_entry = {"task": "regression", "source": "openml-ctr23"}
    pmlb_entry = {"task": "regression", "source": "pmlb"}

    assert expected_evaluations(openml_entry, 5, 1) == 2 * expected_evaluations(
        pmlb_entry, 5, 1
    )


def big_frame(rows: int):
    return (
        pd.DataFrame({"a": np.arange(rows, dtype=float), "b": np.arange(rows) * 2.0}),
        np.arange(rows),
    )


def five_folds(rows: int):
    index = np.arange(rows)
    return from_openml(
        "big", [(list(index[index % 5 != k]), list(index[index % 5 == k])) for k in range(5)]
    )


def test_a_dataset_within_the_cap_is_untouched():
    from mlsandbox.benchmark import cap_rows

    features, target = big_frame(100)
    folds = five_folds(100)
    capped_features, _, capped_folds = cap_rows(features, target, folds, seed=1)
    assert len(capped_features) == 100
    assert capped_folds.origin == "openml"


def test_a_large_dataset_is_reduced_to_the_cap():
    # A timeout does not save time, it spends its whole budget: SVM on 96,000 rows burns
    # 300 seconds per fold per variant rather than failing fast.
    from mlsandbox.benchmark import EVALUATION_ROW_CAP, cap_rows

    features, target = big_frame(50_000)
    capped, _, _ = cap_rows(features, target, five_folds(50_000), seed=1)
    assert len(capped) == EVALUATION_ROW_CAP


def test_capping_keeps_the_published_partitioning():
    # Subsetting rather than regenerating: a row that survives stays in the fold it was
    # assigned to, so the study does not quietly swap OpenML's splits for its own on the
    # datasets where comparability matters most.
    from mlsandbox.benchmark import cap_rows

    features, target = big_frame(50_000)
    _, _, folds = cap_rows(features, target, five_folds(50_000), seed=1)
    assert folds.origin == "openml, capped"


def test_capped_folds_still_partition_the_data():
    from mlsandbox.benchmark import EVALUATION_ROW_CAP, cap_rows

    features, target = big_frame(50_000)
    capped, _, folds = cap_rows(features, target, five_folds(50_000), seed=1)
    assert folds.covers(EVALUATION_ROW_CAP)
    for train, test in folds.folds:
        assert not set(train) & set(test)


def test_features_and_target_stay_aligned_after_capping():
    # The failure this guards against is silent: shuffled labels produce scores that look
    # like a method performing badly.
    from mlsandbox.benchmark import cap_rows

    features, target = big_frame(50_000)
    capped_features, capped_target, _ = cap_rows(features, target, five_folds(50_000), seed=1)
    assert np.array_equal(capped_features["a"].to_numpy(), capped_target.astype(float))


def test_capping_is_reproducible():
    from mlsandbox.benchmark import cap_rows

    features, target = big_frame(50_000)
    first, _, _ = cap_rows(features, target, five_folds(50_000), seed=3)
    second, _, _ = cap_rows(features, target, five_folds(50_000), seed=3)
    assert first.equals(second)
