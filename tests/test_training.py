"""Live training of the recommended methods on a user's own data (#80, D-053).

The timeout/Stop tests fork rather than spawn: a forked child inherits the parent's
already-monkeypatched module state, which is what lets a fake slow estimator stand in for
a real slow fit deterministically. Production code leaves the platform default alone.
"""

import multiprocessing as mp
import threading
import time

import numpy as np
import pandas as pd
import pytest
from sklearn.base import BaseEstimator
from sklearn.pipeline import Pipeline

import mlsandbox.training as training
from mlsandbox.training import (
    MIN_CLASS_COUNT_FOR_CV,
    NotCrossValidatable,
    TrainingJob,
    _n_folds_for,
    _orchestrate,
    request_stop,
    start,
)

FORK = mp.get_context("fork")


@pytest.fixture
def classification_data():
    rng = np.random.default_rng(0)
    features = pd.DataFrame(rng.normal(size=(60, 3)), columns=["a", "b", "c"])
    target = (rng.random(60) > 0.5).astype(int)
    return features, target


class Slow(BaseEstimator):
    """Stands in for a method whose `fit` never returns on its own within the test's
    timeout — deterministic, unlike waiting on a real estimator to be slow enough."""

    def fit(self, _x, _y):
        time.sleep(5)
        return self

    def predict(self, x):
        return np.zeros(len(x))


def run_job(methods, task, data, *, seed=0, context=FORK) -> TrainingJob:
    features, target = data
    job = TrainingJob(id="test", methods=list(methods), task=task)
    _orchestrate(job, features, target, seed, context)
    return job


def test_a_successful_run_scores_every_method_and_keeps_the_fitted_pipeline(
    classification_data,
):
    job = run_job(["logistic_regression", "naive_bayes"], "classification", classification_data)

    assert job.done
    assert not job.aborted
    for method in ["logistic_regression", "naive_bayes"]:
        result = job.results[method]
        assert result.status == "ok"
        assert result.mean_score is not None
        assert len(result.fold_scores) > 1
        assert result.fitted is not None


def test_an_unknown_method_aborts_the_job_rather_than_skipping_it(classification_data):
    # A fit error is different from a timeout: FR-8.4 asks a timeout to skip and continue,
    # but an error (a column type a method cannot handle, say) can implicate the dataset
    # itself, not just one method — so the whole run stops rather than quietly hiding it.
    job = run_job(["no_such_method"], "classification", classification_data)

    assert job.aborted
    assert "no_such_method" in job.abort_detail
    assert job.results["no_such_method"].status == "error"


def test_a_method_that_overruns_is_killed_and_marked_timed_out(
    classification_data, monkeypatch
):
    monkeypatch.setattr(training, "build", lambda *_a, **_k: Pipeline([("model", Slow())]))
    monkeypatch.setattr(training, "timeout_for", lambda *_a, **_k: 1)

    job = run_job(["logistic_regression"], "classification", classification_data)

    result = job.results["logistic_regression"]
    assert result.status == "timeout"
    assert "exceeded 1s" in result.detail
    assert result.fitted is None
    assert not job.aborted


def test_a_timeout_does_not_abort_the_job_the_next_method_still_runs(
    classification_data, monkeypatch
):
    real_build = training.build

    def fake_build(name, task, *, seed=0):
        if name == "slow_one":
            return Pipeline([("model", Slow())])
        return real_build(name, task, seed=seed)

    monkeypatch.setattr(training, "build", fake_build)
    monkeypatch.setattr(training, "timeout_for", lambda *_a, **_k: 1)

    job = run_job(["slow_one", "naive_bayes"], "classification", classification_data)

    assert job.results["slow_one"].status == "timeout"
    assert job.results["naive_bayes"].status == "ok"
    assert not job.aborted


def test_stopping_mid_run_ends_the_current_method_and_trains_nothing_further(
    classification_data, monkeypatch
):
    features, target = classification_data
    monkeypatch.setattr(training, "build", lambda *_a, **_k: Pipeline([("model", Slow())]))
    job = TrainingJob(
        id="test", methods=["logistic_regression", "naive_bayes"], task="classification"
    )

    def stop_soon():
        time.sleep(0.3)
        request_stop(job)

    threading.Thread(target=stop_soon).start()
    _orchestrate(job, features, target, 0, FORK)

    assert job.done
    assert job.results["logistic_regression"].status == "stopped"
    assert "naive_bayes" not in job.results


def test_halts_early_once_the_top_three_no_longer_distinguish_themselves(classification_data):
    # Five cheap, comparable methods on the same easy dataset should converge well before
    # the fifth — real behaviour, not a monkeypatched shortcut.
    job = run_job(
        ["logistic_regression", "naive_bayes", "lda", "qda", "decision_tree"],
        "classification",
        classification_data,
    )

    assert job.done
    assert len(job.results) <= 5
    if job.halted_early:
        assert len(job.results) == 3


def test_a_rare_class_below_the_floor_is_reported_before_any_subprocess_starts(
    classification_data,
):
    features, target = classification_data
    target = target.copy()
    target[:] = 0
    target[0] = 1  # exactly one example of the rare class — below MIN_CLASS_COUNT_FOR_CV

    job = TrainingJob(id="test", methods=["logistic_regression"], task="classification")
    _orchestrate(job, features, target, 0, FORK)

    assert job.aborted
    assert "rarest class" in job.abort_detail
    assert job.results == {}


def test_n_folds_is_capped_at_five_and_never_exceeds_the_rarest_class():
    target = np.array([0] * 3 + [1] * 100)
    n_folds, stratified = _n_folds_for(target, "classification")
    assert stratified
    assert n_folds == 3


def test_regression_always_uses_five_folds_unstratified():
    target = np.linspace(0, 1, 20)
    n_folds, stratified = _n_folds_for(target, "regression")
    assert n_folds == 5
    assert not stratified


def test_a_class_below_the_floor_raises_before_any_fold_is_built():
    target = np.array([0] * (MIN_CLASS_COUNT_FOR_CV - 1) + [1] * 50)
    with pytest.raises(NotCrossValidatable):
        _n_folds_for(target, "classification")


def test_start_returns_immediately_and_the_job_progresses_in_the_background(
    classification_data,
):
    features, target = classification_data
    job = start(["logistic_regression"], "classification", features, target, context=FORK)

    assert not job.done  # the call did not block for the fit to finish

    for _ in range(100):
        if job.snapshot()["done"]:
            break
        time.sleep(0.05)

    snapshot = job.snapshot()
    assert snapshot["done"]
    assert snapshot["results"]["logistic_regression"].status == "ok"
