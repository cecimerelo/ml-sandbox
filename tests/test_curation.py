"""Selection rules, tested without touching the network.

These matter more than typical unit tests: the rules decide which datasets the thesis
draws conclusions from, so a silent mistake here biases every result downstream.
"""

import pytest

from mlsandbox.curation import (
    MAX_FEATURES,
    SMALL_BAND_MAX_ROWS,
    coverage,
    family_of,
    screen,
    screen_one,
)
from mlsandbox.openml_client import DatasetMetadata


def make(
    dataset_id: int = 1,
    name: str = "example",
    rows: int = 200,
    features: int = 10,
    classes: int = 2,
    missing_values: int = 0,
    categorical_features: int = 0,
) -> DatasetMetadata:
    return DatasetMetadata(
        dataset_id=dataset_id,
        name=name,
        version=1,
        rows=rows,
        features=features,
        classes=classes,
        missing_values=missing_values,
        categorical_features=categorical_features,
        licence="public",
    )


def test_keeps_a_small_tabular_dataset():
    assert screen_one(make(rows=200, features=10)) is None


def test_rejects_above_the_feature_cap():
    reason = screen_one(make(features=MAX_FEATURES + 1))
    assert reason is not None
    assert "NFR-2" in reason


def test_keeps_exactly_at_the_feature_cap():
    assert screen_one(make(features=MAX_FEATURES)) is None


def test_rejects_image_derived_even_under_the_cap():
    # The cap would normally catch these; the explicit list keeps the intent visible and
    # catches any that would slip under it.
    reason = screen_one(make(name="mnist_784", features=10))
    assert reason is not None
    assert "image" in reason


def test_rejects_missing_row_count():
    assert screen_one(make(rows=0)) is not None


def test_require_small_rejects_datasets_already_covered_by_the_suites():
    reason = screen_one(make(rows=SMALL_BAND_MAX_ROWS), require_small=True)
    assert reason is not None
    assert "already covered" in reason


def test_require_small_keeps_just_below_the_threshold():
    assert screen_one(make(rows=SMALL_BAND_MAX_ROWS - 1), require_small=True) is None


def test_large_datasets_are_fine_when_small_is_not_required():
    # D-005: the benchmark imposes no row ceiling.
    assert screen_one(make(rows=90_000)) is None


@pytest.mark.parametrize(
    ("left", "right"),
    [
        ("one-hundred-plants-margin", "one-hundred-plants-shape"),
        ("analcatdata_authorship", "analcatdata_boxing"),
    ],
)
def test_relatives_share_a_family(left, right):
    assert family_of(left) == family_of(right)


def test_unrelated_datasets_do_not_collide():
    assert family_of("credit-g") != family_of("diabetes")


def test_only_one_member_of_a_family_survives():
    screening = screen(
        [
            make(1, "one-hundred-plants-margin"),
            make(2, "one-hundred-plants-shape"),
            make(3, "one-hundred-plants-texture"),
        ]
    )
    assert len(screening.kept) == 1
    assert len(screening.excluded) == 2
    assert all("family" in e.reason for e in screening.excluded)


def test_family_slot_is_not_spent_on_a_dataset_that_fails_anyway():
    # The oversized member must not occupy the family's single slot and push out a usable
    # sibling.
    screening = screen(
        [
            make(1, "plants-margin", features=MAX_FEATURES + 1),
            make(2, "plants-shape", features=10),
        ]
    )
    assert [m.dataset_id for m in screening.kept] == [2]


def test_every_candidate_is_either_kept_or_explained():
    candidates = [
        make(1, "good", rows=100),
        make(2, "toobig", features=MAX_FEATURES + 1),
        make(3, "mnist_784"),
    ]
    screening = screen(candidates)
    assert screening.total == len(candidates)
    assert all(e.reason for e in screening.excluded)


def test_order_is_stable_regardless_of_input_order():
    a = make(5, "alpha")
    b = make(2, "beta")
    assert [m.dataset_id for m in screen([a, b]).kept] == [2, 5]
    assert [m.dataset_id for m in screen([b, a]).kept] == [2, 5]


def test_coverage_reports_a_zero_for_an_uncovered_band():
    # The finding that started D-006: the curated suites contain nothing below 500 rows,
    # so the recommender's most distinctive advice would go unvalidated.
    report = coverage([make(1, "a", rows=2000), make(2, "b", rows=50_000)])
    assert report["rows < 500"] == 0


def test_coverage_counts_characteristics_the_recommender_reasons_about():
    report = coverage(
        [
            make(1, "a", rows=100, classes=3, missing_values=5, categorical_features=2),
            make(2, "b", rows=1000, classes=0),
        ]
    )
    assert report["rows < 500"] == 1
    assert report["multiclass"] == 1
    assert report["regression"] == 1
    assert report["has missing values"] == 1
    assert report["has categorical features"] == 1
