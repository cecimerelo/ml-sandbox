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
