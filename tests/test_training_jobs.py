"""The training job record and its in-memory registry (#80, D-053)."""

import time

import pytest

import mlsandbox.training_jobs as training_jobs
from mlsandbox.training_jobs import TrainingJob, get, register


@pytest.fixture(autouse=True)
def clean_registry():
    """Every test starts and ends with an empty registry — otherwise a job `register`ed
    in one test is still there (and could satisfy a `get` that should have failed) in the
    next, since `_REGISTRY` is module-level, shared state."""
    training_jobs._REGISTRY.clear()
    yield
    training_jobs._REGISTRY.clear()


def job(**overrides) -> TrainingJob:
    defaults = {
        "id": "job-1",
        "methods": ["logistic_regression"],
        "task": "classification",
        "budget_seconds": 60,
    }
    return TrainingJob(**{**defaults, **overrides})


def test_an_unknown_job_id_is_simply_absent():
    assert get("no-such-job") is None


def test_a_finished_job_survives_until_its_ttl_elapses(monkeypatch):
    running = job()
    running.mark_done()
    register(running)

    assert get("job-1") is running

    # Still within the TTL: unaffected by the sweep that runs on every register/get.
    monkeypatch.setattr(training_jobs, "JOB_TTL_SECONDS", 3600)
    assert get("job-1") is running


def test_a_finished_job_is_evicted_once_its_ttl_elapses(monkeypatch):
    finished = job()
    finished.mark_done()
    finished.completed_at = time.monotonic() - 1  # finished "1 second ago"
    register(finished)

    monkeypatch.setattr(training_jobs, "JOB_TTL_SECONDS", 0)  # anything finished is expired

    assert get("job-1") is None


def test_an_unfinished_job_is_never_evicted_no_matter_how_old(monkeypatch):
    # completed_at is None until done — a running job has no completion time to measure
    # a TTL from, so nothing here can mistake "still training" for "abandoned".
    running = job()
    register(running)

    monkeypatch.setattr(training_jobs, "JOB_TTL_SECONDS", 0)

    assert get("job-1") is running


def test_mark_done_records_a_completion_timestamp():
    running = job()
    assert running.completed_at is None

    running.mark_done()

    assert running.done
    assert running.completed_at is not None


def test_mark_done_clears_current_even_on_an_early_exit():
    # Regression: an early halt/abort/stop set `done` without clearing `current`, so the
    # frontend (which reads `current == method` as "still fitting", ahead of an already
    # `ok` result) showed that method spinning forever after the job had finished.
    running = job()
    running.current = "random_forest"

    running.mark_done()

    assert running.current is None


def test_snapshot_is_a_copy_not_the_live_results_dict():
    running = job()
    snapshot = running.snapshot()
    running.results["logistic_regression"] = "sneaked in after the snapshot"

    assert snapshot["results"] == {}


def test_snapshot_carries_the_budget_seconds_the_frontend_estimates_from():
    assert job(budget_seconds=120).snapshot()["budget_seconds"] == 120
