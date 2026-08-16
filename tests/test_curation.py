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
from mlsandbox.dataset import Dataset


def make(
    name: str = "example",
    rows: int = 200,
    predictors: int = 10,
    classes: int = 2,
    task: str = "classification",
    missing_values: int | None = 0,
    categorical_predictors: int = 0,
) -> Dataset:
    return Dataset(
        name=name,
        source="test",
        revision="fixed",
        rows=rows,
        predictors=predictors,
        classes=classes,
        task=task,
        missing_values=missing_values,
        categorical_predictors=categorical_predictors,
    )


def test_keeps_a_small_tabular_dataset():
    assert screen_one(make(rows=200, predictors=10)) is None


def test_rejects_above_the_feature_cap():
    reason = screen_one(make(predictors=MAX_FEATURES + 1))
    assert reason is not None
    assert "NFR-2" in reason


def test_keeps_exactly_at_the_feature_cap():
    assert screen_one(make(predictors=MAX_FEATURES)) is None


def test_rejects_image_derived_even_under_the_cap():
    # The cap would normally catch these; the explicit list keeps the intent visible and
    # catches any that would slip under it.
    reason = screen_one(make(name="mnist_784", predictors=10))
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
            make("one-hundred-plants-margin"),
            make("one-hundred-plants-shape"),
            make("one-hundred-plants-texture"),
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
            make("plants-margin", predictors=MAX_FEATURES + 1),
            make("plants-shape", predictors=10),
        ]
    )
    assert [m.name for m in screening.kept] == ["plants-shape"]


def test_every_candidate_is_either_kept_or_explained():
    candidates = [
        make("good", rows=100),
        make("toobig", predictors=MAX_FEATURES + 1),
        make("mnist_784"),
    ]
    screening = screen(candidates)
    assert screening.total == len(candidates)
    assert all(e.reason for e in screening.excluded)


def test_order_is_stable_regardless_of_input_order():
    a = make("alpha")
    b = make("beta")
    assert [m.name for m in screen([a, b]).kept] == ["alpha", "beta"]
    assert [m.name for m in screen([b, a]).kept] == ["alpha", "beta"]


def test_coverage_reports_a_zero_for_an_uncovered_band():
    # The finding that started D-006: the curated suites contain nothing below 500 rows,
    # so the recommender's most distinctive advice would go unvalidated.
    report = coverage([make("a", rows=2000), make("b", rows=50_000)])
    assert report["rows < 500"] == 0


def test_coverage_counts_characteristics_the_recommender_reasons_about():
    report = coverage(
        [
            make("a", rows=100, classes=3, missing_values=5, categorical_predictors=2),
            make("b", rows=1000, classes=0, task="regression"),
        ]
    )
    assert report["rows < 500"] == 1
    assert report["multiclass"] == 1
    assert report["regression"] == 1
    assert report["has missing values"] == 1
    assert report["has categorical features"] == 1


def test_multiclass_count_ignores_regression_datasets():
    # PMLB does not zero n_classes for regression, so a regression dataset can report
    # classes > 2. Counting on that alone files it as multiclass, which is how the
    # earlier task-detection bug stayed invisible.
    report = coverage(
        [
            make("reg", classes=7, task="regression"),
            make("clf", classes=3, task="classification"),
        ]
    )
    assert report["multiclass"] == 1
    assert report["regression"] == 1


def test_stratified_sample_keeps_every_band_populated():
    from mlsandbox.curation import stratified_sample

    datasets = (
        [make(f"s{i}", rows=100) for i in range(15)]
        + [make(f"m{i}", rows=5_000) for i in range(15)]
        + [make(f"l{i}", rows=50_000) for i in range(15)]
    )
    sampled = stratified_sample(datasets, per_stratum=5, seed=1)

    report = coverage(sampled.kept)
    assert report["rows < 500"] == 5
    assert report["rows 500-10k"] == 5
    assert report["rows > 10k"] == 5


def test_stratified_sample_is_reproducible():
    from mlsandbox.curation import stratified_sample

    datasets = [make(f"d{i}", rows=100) for i in range(20)]
    first = stratified_sample(datasets, per_stratum=5, seed=42)
    second = stratified_sample(datasets, per_stratum=5, seed=42)
    assert [d.name for d in first.kept] == [d.name for d in second.kept]


def test_stratified_sample_explains_what_it_dropped():
    from mlsandbox.curation import stratified_sample

    datasets = [make(f"d{i}", rows=100) for i in range(10)]
    sampled = stratified_sample(datasets, per_stratum=3, seed=1)
    assert len(sampled.kept) == 3
    assert len(sampled.excluded) == 7
    assert all("not sampled" in e.reason for e in sampled.excluded)
