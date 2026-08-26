"""Result storage and resumption.

A full run is hours. Losing it to a crash at hour five, or silently mixing results from
two different configurations, are the two failures this has to prevent.
"""

import pytest

from mlsandbox.results import Result, ResultStore, run_key


def result(dataset="d", method="knn", rate=0.0, fold=0, status="ok", score=0.9) -> Result:
    return Result(
        dataset=dataset,
        source="pmlb",
        method=method,
        task="classification",
        missing_rate=rate,
        fold=fold,
        fold_origin="generated",
        status=status,
        score=score,
    )


@pytest.fixture
def store(tmp_path) -> ResultStore:
    return ResultStore(tmp_path, key="abc123")


def test_nothing_is_completed_before_anything_is_written(store):
    assert store.completed() == set()


def test_flushed_results_are_reported_as_completed(store):
    store.add(result())
    store.flush()
    assert result().key in store.completed()


def test_a_resumed_run_skips_what_is_already_there(store):
    store.add(result(fold=0))
    store.add(result(fold=1))
    store.flush()

    done = store.completed()
    remaining = [f for f in range(5) if result(fold=f).key not in done]
    assert remaining == [2, 3, 4]


def test_flushing_twice_appends_rather_than_replaces(store):
    store.add(result(fold=0))
    store.flush()
    store.add(result(fold=1))
    store.flush()
    assert len(store.load()) == 2


def test_flushing_nothing_is_harmless(store):
    assert store.flush() == 0


def test_timeouts_count_as_completed(store):
    # Re-running a timeout spends the same minutes to reach the same outcome. Deleting the
    # file is how a retry is requested.
    store.add(result(status="timeout", score=None))
    store.flush()
    assert result().key in store.completed()


def test_a_timeout_stores_no_score(store):
    # Scoring a timeout as zero would let a slow method rank below a bad one, which is a
    # different claim than "this did not finish".
    store.add(result(status="timeout", score=None))
    store.flush()
    assert store.load()["score"].isna().all()


def test_a_changed_configuration_writes_somewhere_else(tmp_path):
    # Results from different seeds are not interchangeable, and mixing them is invisible —
    # the table looks complete either way.
    first = ResultStore(tmp_path, key=run_key({"seed": 1, "folds": 10}))
    second = ResultStore(tmp_path, key=run_key({"seed": 2, "folds": 10}))
    assert first.path != second.path


def test_the_same_configuration_writes_to_the_same_place(tmp_path):
    settings = {"seed": 1, "folds": 10}
    assert ResultStore(tmp_path, key=run_key(settings)).path == (
        ResultStore(tmp_path, key=run_key(settings)).path
    )


def test_key_ignores_the_order_the_settings_are_given_in():
    assert run_key({"a": 1, "b": 2}) == run_key({"b": 2, "a": 1})
