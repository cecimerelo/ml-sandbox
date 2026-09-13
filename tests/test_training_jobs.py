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


def test_an_unknown_job_id_is_simply_absent():
    assert get("no-such-job") is None


def test_a_finished_job_survives_until_its_ttl_elapses(monkeypatch):
    job = TrainingJob(id="job-1", methods=["logistic_regression"], task="classification")
    job.mark_done()
    register(job)

    assert get("job-1") is job

    # Still within the TTL: unaffected by the sweep that runs on every register/get.
    monkeypatch.setattr(training_jobs, "JOB_TTL_SECONDS", 3600)
    assert get("job-1") is job


def test_a_finished_job_is_evicted_once_its_ttl_elapses(monkeypatch):
    job = TrainingJob(id="job-1", methods=["logistic_regression"], task="classification")
    job.mark_done()
    job.completed_at = time.monotonic() - 1  # finished "1 second ago"
    register(job)

    monkeypatch.setattr(training_jobs, "JOB_TTL_SECONDS", 0)  # anything finished is expired

    assert get("job-1") is None


def test_an_unfinished_job_is_never_evicted_no_matter_how_old(monkeypatch):
    # completed_at is None until done — a running job has no completion time to measure
    # a TTL from, so nothing here can mistake "still training" for "abandoned".
    job = TrainingJob(id="job-1", methods=["logistic_regression"], task="classification")
    register(job)

    monkeypatch.setattr(training_jobs, "JOB_TTL_SECONDS", 0)

    assert get("job-1") is job


def test_mark_done_records_a_completion_timestamp():
    job = TrainingJob(id="job-1", methods=["logistic_regression"], task="classification")
    assert job.completed_at is None

    job.mark_done()

    assert job.done
    assert job.completed_at is not None


def test_snapshot_is_a_copy_not_the_live_results_dict():
    job = TrainingJob(id="job-1", methods=["logistic_regression"], task="classification")
    snapshot = job.snapshot()
    job.results["logistic_regression"] = "sneaked in after the snapshot"

    assert snapshot["results"] == {}
