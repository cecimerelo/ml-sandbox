"""Column summaries for the EDA block — and the privacy claim they exist to make.

An endpoint that cannot return a row cannot leak one by accident; these tests check that
every summary really is a reduction, never a pass-through.
"""

import numpy as np
import pandas as pd
import pytest

from mlsandbox.eda import (
    BIN_COUNT,
    MAX_CATEGORIES_SHOWN,
    MAX_CORRELATION_FEATURES,
    BoxplotSummary,
    CategoricalBars,
    CorrelationMatrix,
    Histogram,
    column_kinds,
    correlation_matrix,
    summarise_column,
)


def numeric(values) -> pd.Series:
    return pd.Series(values, name="x")


def categorical(values) -> pd.Series:
    return pd.Series(values, name="c")


# Branch selection


def test_a_numeric_column_gets_a_histogram():
    result = summarise_column(numeric([1, 2, 3, 4, 5]))
    assert isinstance(result, Histogram)


def test_a_text_column_gets_bars():
    result = summarise_column(categorical(["red", "blue", "red"]))
    assert isinstance(result, CategoricalBars)


def test_agrees_with_metafeatures_own_numeric_test():
    # The same test `from_dataset` uses, not a second opinion that could drift from it.
    values = numeric([1, 2, 3])
    assert pd.api.types.is_numeric_dtype(values) == isinstance(
        summarise_column(values), Histogram
    )


# Histograms


def test_bins_cover_the_full_range_and_nothing_outside_it():
    result = summarise_column(numeric(range(100)))
    assert isinstance(result, Histogram)
    assert len(result.bins) == BIN_COUNT
    assert result.bins[0].start == pytest.approx(0)
    assert result.bins[-1].end == pytest.approx(99)


def test_every_value_lands_in_exactly_one_bin():
    result = summarise_column(numeric(range(200)))
    assert isinstance(result, Histogram)
    assert sum(b.count for b in result.bins) == 200


def test_a_constant_column_is_one_bin_not_an_arbitrary_width():
    result = summarise_column(numeric([7.0] * 10))
    assert isinstance(result, Histogram)
    assert len(result.bins) == 1
    assert result.bins[0].start == result.bins[0].end == 7.0
    assert result.bins[0].count == 10


def test_missing_values_are_counted_not_binned():
    result = summarise_column(numeric([1, 2, np.nan, 4, np.nan]))
    assert isinstance(result, Histogram)
    assert result.missing == 2
    assert sum(b.count for b in result.bins) == 3


def test_a_boolean_column_is_summarised_not_a_crash():
    # `is_numeric_dtype` counts bool as numeric, correctly — a `has_garden` column is a
    # 0/1 measurement, not a category — but numpy's own quantile machinery cannot
    # subtract two bools to interpolate between them, which crashed the whole endpoint
    # the one time this shipped without a cast.
    result = summarise_column(pd.Series([True, False, True, True], name="has_garden"))
    assert isinstance(result, Histogram)
    assert result.boxplot is not None
    assert result.boxplot.median == 1.0


def test_an_all_missing_column_is_reported_not_divided_by_zero():
    result = summarise_column(numeric([np.nan, np.nan]))
    assert isinstance(result, Histogram)
    assert result.bins == []
    assert result.missing == 2


def test_a_histogram_never_carries_a_raw_value():
    # The privacy claim, checked structurally: nothing on the model can hold a value
    # that was in the column, only edges and counts.
    assert set(Histogram.model_fields) == {"column", "kind", "bins", "missing", "boxplot"}


# Categorical bars


def test_categories_are_ordered_by_frequency():
    values = categorical(["a"] * 1 + ["b"] * 5 + ["c"] * 3)
    result = summarise_column(values)
    assert isinstance(result, CategoricalBars)
    assert [c.category for c in result.categories] == ["b", "c", "a"]


def test_at_or_under_the_cap_nothing_folds():
    values = categorical([f"cat-{i}" for i in range(MAX_CATEGORIES_SHOWN)])
    result = summarise_column(values)
    assert isinstance(result, CategoricalBars)
    assert len(result.categories) == MAX_CATEGORIES_SHOWN
    assert result.other_count == 0
    assert result.other_categories == 0


def test_above_the_cap_the_tail_folds_into_other():
    # One row each for 20 categories — 15 shown, 5 folded.
    values = categorical([f"cat-{i}" for i in range(20)])
    result = summarise_column(values)
    assert isinstance(result, CategoricalBars)
    assert len(result.categories) == MAX_CATEGORIES_SHOWN
    assert result.other_categories == 5
    assert result.other_count == 5


def test_the_fold_is_never_silent():
    # `other_categories` is the N in "Other (N categories)" — always present when
    # anything folded, so the interface always has something to name it with.
    values = categorical([f"cat-{i}" for i in range(30)])
    result = summarise_column(values)
    assert isinstance(result, CategoricalBars)
    assert result.other_categories > 0


def test_missing_values_are_counted_not_a_category():
    values = categorical(["a", "b", None, "a", None])
    result = summarise_column(values)
    assert isinstance(result, CategoricalBars)
    assert result.missing == 2
    assert sum(c.count for c in result.categories) == 3


def test_bars_never_carry_a_raw_row():
    # Categories are distinct *values*, already the reduction — never a per-row list.
    assert set(CategoricalBars.model_fields) == {
        "column",
        "kind",
        "categories",
        "other_count",
        "other_categories",
        "missing",
    }


# The feature picker's inventory


def test_column_kinds_excludes_the_target():
    frame = pd.DataFrame({"a": [1, 2], "b": ["x", "y"], "target": [0, 1]})
    kinds = column_kinds(frame, target="target")
    assert [k.column for k in kinds] == ["a", "b"]


def test_column_kinds_matches_each_column_to_its_chart_form():
    frame = pd.DataFrame({"a": [1, 2], "b": ["x", "y"]})
    kinds = {k.column: k.kind for k in column_kinds(frame, target="__none__")}
    assert kinds == {"a": "numeric", "b": "categorical"}


def test_column_kinds_preserves_the_frames_own_order():
    frame = pd.DataFrame({"z": [1], "a": [1], "m": [1], "t": [1]})
    kinds = column_kinds(frame, target="t")
    assert [k.column for k in kinds] == ["z", "a", "m"]


# Boxplots


def test_the_five_number_summary_is_correct():
    result = summarise_column(numeric([1, 2, 3, 4, 5, 6, 7, 8, 9]))
    assert isinstance(result, Histogram)
    box = result.boxplot
    assert box is not None
    assert box.minimum == 1
    assert box.median == 5
    assert box.maximum == 9


def test_a_point_beyond_the_fence_is_an_outlier_not_the_new_maximum():
    # 1.5x IQR beyond Q3 is the conventional fence (Tukey). 100 is far past it.
    result = summarise_column(numeric([1, 2, 3, 4, 5, 6, 7, 8, 9, 100]))
    assert isinstance(result, Histogram)
    box = result.boxplot
    assert box is not None
    assert 100 in box.outliers
    assert box.maximum < 100


def test_a_constant_column_has_no_outliers():
    result = summarise_column(numeric([5.0] * 10))
    assert isinstance(result, Histogram)
    box = result.boxplot
    assert box is not None
    assert box.outliers == []
    assert box.minimum == box.maximum == 5.0


def test_an_all_missing_column_has_no_boxplot_either():
    result = summarise_column(numeric([np.nan, np.nan]))
    assert isinstance(result, Histogram)
    assert result.boxplot is None


def test_a_boxplot_never_carries_a_raw_row():
    # Individual values, yes (same class of disclosure as a histogram's bin edges) —
    # but never anything that ties one column's value to another's in the same row.
    assert set(BoxplotSummary.model_fields) == {
        "minimum",
        "q1",
        "median",
        "q3",
        "maximum",
        "outliers",
    }


# The correlation heatmap


def test_perfectly_correlated_columns_read_as_one():
    frame = pd.DataFrame({"a": [1, 2, 3, 4], "b": [2, 4, 6, 8]})
    result = correlation_matrix(frame, exclude="__none__")
    i, j = result.features.index("a"), result.features.index("b")
    assert result.values[i][j] == pytest.approx(1.0)


def test_the_diagonal_is_always_one():
    frame = pd.DataFrame({"a": [1, 2, 3], "b": [3, 1, 2], "c": [5, 5, 1]})
    result = correlation_matrix(frame, exclude="__none__")
    for i in range(len(result.features)):
        assert result.values[i][i] == pytest.approx(1.0)


def test_the_target_is_excluded():
    frame = pd.DataFrame({"a": [1, 2, 3], "b": [3, 2, 1], "target": [1, 0, 1]})
    result = correlation_matrix(frame, exclude="target")
    assert "target" not in result.features


def test_categorical_columns_are_excluded():
    frame = pd.DataFrame({"a": [1, 2, 3], "b": [3, 2, 1], "c": ["x", "y", "z"]})
    result = correlation_matrix(frame, exclude="__none__")
    assert "c" not in result.features


def test_fewer_than_two_numeric_features_is_empty_not_an_error():
    frame = pd.DataFrame({"a": [1, 2, 3], "b": ["x", "y", "z"]})
    result = correlation_matrix(frame, exclude="__none__")
    assert result.features == []
    assert result.values == []
    assert result.total_numeric == 1


def test_all_categorical_data_is_the_same_empty_state():
    frame = pd.DataFrame({"a": ["x", "y"], "b": ["p", "q"]})
    result = correlation_matrix(frame, exclude="__none__")
    assert result.features == []
    assert result.total_numeric == 0


def test_a_constant_column_correlates_as_zero_not_nan():
    # pandas' own answer is NaN — undefined, not zero — but NaN is not valid JSON and
    # not a value a heatmap cell can render. Read as "no signal", which is what a
    # constant column actually has.
    frame = pd.DataFrame({"a": [1, 2, 3], "constant": [5, 5, 5]})
    result = correlation_matrix(frame, exclude="__none__")
    i, j = result.features.index("a"), result.features.index("constant")
    assert result.values[i][j] == 0.0


def test_the_cap_keeps_the_highest_variance_features():
    columns = {f"low-{i}": [1, 1, 1, 2] for i in range(35)}
    columns["high-variance"] = [1, 1000, -1000, 500]
    frame = pd.DataFrame(columns)
    result = correlation_matrix(frame, exclude="__none__")
    assert len(result.features) == MAX_CORRELATION_FEATURES
    assert "high-variance" in result.features
    assert result.total_numeric == 36


def test_states_the_total_against_the_cap():
    columns = {f"f-{i}": [1, 2, 3] for i in range(40)}
    frame = pd.DataFrame(columns)
    result = correlation_matrix(frame, exclude="__none__")
    assert len(result.features) == MAX_CORRELATION_FEATURES
    assert result.total_numeric == 40


def test_a_correlation_matrix_never_carries_a_raw_row():
    assert set(CorrelationMatrix.model_fields) == {"features", "values", "total_numeric"}
