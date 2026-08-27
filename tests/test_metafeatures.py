"""The seven inputs Layer 2 learns from.

Two properties matter more than the individual bands. The upload path and the no-dataset
path must produce the same representation for the same problem, or the model is served
something it never trained on. And a value that does not apply must say so rather than
default to something meaningless.
"""

import numpy as np
import pandas as pd
import pytest

from mlsandbox.metafeatures import (
    band_class_balance,
    band_feature_types,
    band_missing,
    band_regime,
    band_task,
    from_dataset,
    from_form,
)


def frame(rows: int, columns: int, categorical: int = 0) -> pd.DataFrame:
    rng = np.random.default_rng(0)
    data = {f"n{i}": rng.normal(size=rows) for i in range(columns - categorical)}
    data.update({f"c{i}": rng.choice(["a", "b"], size=rows) for i in range(categorical)})
    return pd.DataFrame(data)


def test_task_keeps_binary_and_multiclass_apart():
    # FR-1.3 asks for three values. Collapsing to two would discard something the user
    # already told us, and it changes the answer: several methods handle many classes
    # poorly.
    assert band_task("classification", 2) == "binary classification"
    assert band_task("classification", 7) == "multiclass classification"
    assert band_task("regression", None) == "regression"


@pytest.mark.parametrize(
    ("rows", "features", "expected"),
    [
        ("<500", ">50", "high-dimensional"),
        ("500-10k", "10-50", "moderate"),
        (">10k", "<10", "data-rich"),
    ],
)
def test_regime_separates_the_opposite_extremes(rows, features, expected):
    # The pair of bands implies this, but only through an interaction between categorical
    # variables — which sixty training rows cannot be relied on to discover.
    assert band_regime(rows, features) == expected


def test_missing_distinguishes_none_from_a_trace():
    assert band_missing(0.0) == "none"
    assert band_missing(0.001) == "some"
    assert band_missing(0.5) == "a lot"


def test_a_single_categorical_column_among_many_is_not_mixed():
    # One categorical column in fifty does not change which method suits the data, and
    # calling it mixed would put almost everything in one band.
    assert band_feature_types(1, 50) == "numeric"
    assert band_feature_types(20, 50) == "mixed"
    assert band_feature_types(10, 10) == "categorical"


def test_class_balance_does_not_apply_to_regression():
    # A default here would hand Layer 2 a value that means nothing.
    assert band_class_balance("regression", np.array([1.0, 2.0])) == "not applicable"


def test_class_balance_detects_a_dominant_class():
    dominant = np.array([0] * 95 + [1] * 5)
    even = np.array([0] * 50 + [1] * 50)
    assert band_class_balance("classification", dominant) == "one class dominates"
    assert band_class_balance("classification", even) == "roughly equal"


def test_both_paths_describe_the_same_problem_identically():
    # The property the whole design rests on: a model trained on one path's output and
    # served the other's must be seeing the same thing.
    features = frame(rows=1_000, columns=20)
    target = np.array([0] * 500 + [1] * 500)

    uploaded = from_dataset(task="classification", features=features, target=target)
    described = from_form(
        task="binary classification",
        rows="500-10k",
        features="10-50",
        feature_types="numeric",
        missing="none",
        class_balance="roughly equal",
    )

    assert uploaded == described


def test_the_form_path_derives_the_regime_rather_than_asking_for_it():
    # Asking a user for observations per predictor would be asking them to do arithmetic
    # they came here to avoid.
    described = from_form(
        task="regression",
        rows="<500",
        features=">50",
        feature_types="numeric",
        missing="none",
        class_balance="not applicable",
    )
    assert described.regime == "high-dimensional"


def test_a_dataset_with_no_columns_does_not_divide_by_zero():
    empty = pd.DataFrame(index=range(10))
    result = from_dataset(task="regression", features=empty)
    assert result.missing == "none"


def test_the_row_is_flat_and_serialisable():
    # It becomes one row of the Layer 2 training table, so every value has to be a plain
    # string.
    row = from_dataset(task="regression", features=frame(100, 5)).as_row()
    assert len(row) == 7
    assert all(isinstance(v, str) for v in row.values())


def test_every_band_combination_has_a_regime():
    # Nine cells, stated rather than computed. A missing one would raise at run time, on a
    # user's dataset, rather than here.
    from mlsandbox.metafeatures import REGIME_BY_BANDS

    rows = ("<500", "500-10k", ">10k")
    features = ("<10", "10-50", ">50")
    assert set(REGIME_BY_BANDS) == {(r, f) for r in rows for f in features}


@pytest.mark.parametrize(
    ("rows", "features"),
    [("<500", "<10"), ("<500", ">50"), ("500-10k", "10-50"), (">10k", ">50")],
)
def test_both_paths_agree_across_the_band_grid(rows, features):
    # The property the design rests on, checked at the corners rather than one example.
    from mlsandbox.metafeatures import BAND_EXAMPLES

    n_rows, n_features = BAND_EXAMPLES[rows], BAND_EXAMPLES[features]
    uploaded = from_dataset(task="regression", features=frame(n_rows, n_features))
    described = from_form(
        task="regression",
        rows=rows,
        features=features,
        feature_types="numeric",
        missing="none",
        class_balance="not applicable",
    )
    assert uploaded == described
