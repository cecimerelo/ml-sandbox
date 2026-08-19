"""The fetch-verification path.

This code only runs when something has gone wrong, which is exactly when nobody wants to
discover it never worked. #8 requires that a dataset which cannot be retrieved is recorded
with a reason rather than taking down the run.
"""

import pandas as pd
import pytest

from scripts.build_collection import fetch_all


def frame(*, rows: int, predictors: int) -> pd.DataFrame:
    columns = {f"x{i}": range(rows) for i in range(predictors)}
    columns["target"] = range(rows)
    return pd.DataFrame(columns)


def entry(name: str, *, rows: int = 2, predictors: int = 1) -> dict:
    return {"name": name, "rows": rows, "predictors": predictors, "source": "pmlb"}


@pytest.fixture
def manifest() -> dict:
    return {"datasets": [entry("good"), entry("bad")]}


def test_a_download_failure_is_recorded_not_raised(manifest, config, monkeypatch):
    def load(dataset, _config):
        if dataset["name"] == "bad":
            raise ConnectionError("server said no")
        return frame(rows=2, predictors=1)

    monkeypatch.setattr("scripts.build_collection.load_any", load)

    fetched, failures = fetch_all(manifest, config)

    assert fetched == 1
    assert [f["name"] for f in failures] == ["bad"]
    assert "server said no" in failures[0]["reason"]


def test_one_bad_dataset_does_not_stop_the_others(manifest, config, monkeypatch):
    attempted = []

    def load(dataset, _config):
        attempted.append(dataset["name"])
        if dataset["name"] == "good":
            raise ValueError("boom")
        return frame(rows=2, predictors=1)

    monkeypatch.setattr("scripts.build_collection.load_any", load)

    fetch_all(manifest, config)

    # The failing dataset comes first; the second must still be attempted.
    assert attempted == ["good", "bad"]


def test_a_row_count_mismatch_is_a_failure(manifest, config, monkeypatch):
    # Rows are the hard invariant. A dataset that downloads with the wrong number of them
    # is not the dataset the manifest describes.
    monkeypatch.setattr(
        "scripts.build_collection.load_any",
        lambda _dataset, _config: frame(rows=99, predictors=1),
    )

    fetched, failures = fetch_all(manifest, config)

    assert fetched == 0
    assert all("rows on disk" in f["reason"] for f in failures)


def test_a_column_count_mismatch_corrects_the_manifest(config, monkeypatch):
    # OpenML counts row-identifier and ignored attributes in NumberOfFeatures, which the
    # loader drops — so the index can legitimately over-count. The data wins, and the
    # disagreement is recorded rather than absorbed.
    manifest = {"datasets": [entry("climate", rows=2, predictors=20)]}
    monkeypatch.setattr(
        "scripts.build_collection.load_any",
        lambda _dataset, _config: frame(rows=2, predictors=18),
    )

    fetched, failures = fetch_all(manifest, config)

    assert fetched == 1
    assert failures == []
    corrected = manifest["datasets"][0]
    assert corrected["predictors"] == 18
    assert corrected["predictor_count_corrected_from"] == 20


def test_a_matching_dataset_is_not_marked_as_corrected(config, monkeypatch):
    manifest = {"datasets": [entry("fine", rows=2, predictors=1)]}
    monkeypatch.setattr(
        "scripts.build_collection.load_any",
        lambda _dataset, _config: frame(rows=2, predictors=1),
    )

    fetch_all(manifest, config)

    assert "predictor_count_corrected_from" not in manifest["datasets"][0]
