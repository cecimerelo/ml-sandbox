"""The fetch-verification path.

This code only runs when something has gone wrong, which is exactly when nobody wants to
discover it never worked. #8 requires that a dataset which cannot be retrieved is
recorded with a reason rather than taking down the run.
"""

import pytest

from scripts.build_collection import fetch_all


@pytest.fixture
def manifest() -> dict:
    return {
        "datasets": [
            {"name": "good", "rows": 2, "predictors": 1},
            {"name": "bad", "rows": 2, "predictors": 1},
        ]
    }


def test_a_download_failure_is_recorded_not_raised(manifest, config, monkeypatch):
    def load(name, _config):
        if name == "bad":
            raise ConnectionError("server said no")
        return _frame(rows=2, predictors=1)

    monkeypatch.setattr("scripts.build_collection.load_dataset", load)

    fetched, failures = fetch_all(manifest, config)

    assert fetched == 1
    assert [f["name"] for f in failures] == ["bad"]
    assert "server said no" in failures[0]["reason"]


def test_one_bad_dataset_does_not_stop_the_others(manifest, config, monkeypatch):
    calls = []

    def load(name, _config):
        calls.append(name)
        if name == "good":
            raise ValueError("boom")
        return _frame(rows=2, predictors=1)

    monkeypatch.setattr("scripts.build_collection.load_dataset", load)

    fetch_all(manifest, config)

    # The failing dataset comes first; the second must still be attempted.
    assert calls == ["good", "bad"]


def test_a_shape_mismatch_is_a_failure(manifest, config, monkeypatch):
    # A dataset that downloads but disagrees with the index is worse than one that fails
    # outright: it would silently enter the study as something other than what the
    # manifest claims.
    monkeypatch.setattr(
        "scripts.build_collection.load_dataset",
        lambda name, _config: _frame(rows=99, predictors=1),
    )

    fetched, failures = fetch_all(manifest, config)

    assert fetched == 0
    assert len(failures) == 2
    assert all("does not match the index" in f["reason"] for f in failures)


def _frame(*, rows: int, predictors: int):
    import pandas as pd

    columns = {f"x{i}": range(rows) for i in range(predictors)}
    columns["target"] = range(rows)
    return pd.DataFrame(columns)
