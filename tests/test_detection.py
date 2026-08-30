"""Reading a dataset's properties — and refusing to when the reading would be nonsense.

The failure this guards against does not look like a failure. Without the target checks the
detector reports "multiclass, 8,000 classes" for an invoice number and trains models on it,
producing scores that are wrong in a way nothing downstream can notice.
"""

import numpy as np
import pandas as pd
import pytest

from mlsandbox.detection import (
    Detected,
    Unpredictable,
    detect,
    inspect_target,
)


def frame(rows: int = 200, **columns) -> pd.DataFrame:
    rng = np.random.default_rng(0)
    base = {"x": rng.normal(size=rows), "y": rng.normal(size=rows)}
    return pd.DataFrame({**base, **columns})


# Targets that cannot be predicted


def test_an_identifier_is_refused():
    """The one that would otherwise be reported as an 8,000-class problem."""
    data = frame(200, invoice=[f"INV-{i:05d}" for i in range(200)])
    result = inspect_target(data, "invoice")
    assert isinstance(result, Unpredictable)
    assert result.problem == "identifier"
    assert "invoice" in result.message


def test_a_constant_column_is_refused():
    data = frame(200, status=["active"] * 200)
    result = inspect_target(data, "status")
    assert isinstance(result, Unpredictable)
    assert result.problem == "single-value"


def test_a_class_too_rare_to_test_on_is_refused():
    """A score computed over two examples is noise wearing a number."""
    labels = ["common"] * 198 + ["rare"] * 2
    result = inspect_target(frame(200, label=labels), "label")
    assert isinstance(result, Unpredictable)
    assert result.problem == "rare-class"
    assert "2 rows" in result.message


def test_an_all_blank_column_is_refused():
    result = inspect_target(frame(50, blank=[None] * 50), "blank")
    assert isinstance(result, Unpredictable)
    assert result.problem == "empty"


def test_a_missing_column_is_refused_by_name():
    result = inspect_target(frame(50), "nope")
    assert isinstance(result, Unpredictable)
    assert "nope" in result.message


def test_every_refusal_names_the_column():
    """A message about "the target" leaves the user to work out which control to change."""
    cases = [
        (frame(200, ident=[f"a{i}" for i in range(200)]), "ident"),
        (frame(200, flat=["x"] * 200), "flat"),
        (frame(200, rare=["a"] * 197 + ["b"] * 3), "rare"),
    ]
    for data, column in cases:
        result = inspect_target(data, column)
        assert isinstance(result, Unpredictable)
        assert column in result.message


def test_a_continuous_target_with_distinct_values_is_not_an_identifier():
    """Prices are nearly all different and are exactly what regression is for.

    A uniqueness rule that did not exempt continuous values would refuse the most ordinary
    regression problem there is.
    """
    prices = np.linspace(100_000, 500_000, 200) + np.arange(200)
    assert inspect_target(frame(200, price=prices), "price") is None


# What gets read


def test_a_regression_target_is_read_as_one():
    result = detect(frame(200, price=np.linspace(1, 100, 200)), "price")
    assert isinstance(result, Detected)
    assert result.features.task == "regression"
    assert result.n_classes is None


def test_a_label_target_is_read_as_classification():
    result = detect(frame(200, label=["a", "b"] * 100), "label")
    assert isinstance(result, Detected)
    assert result.features.task == "binary classification"
    assert result.n_classes == 2


def test_the_target_is_not_counted_as_a_predictor():
    result = detect(frame(200, price=np.linspace(1, 100, 200)), "price")
    assert isinstance(result, Detected)
    assert result.n_features == 2


def test_the_meta_features_come_from_the_study_not_a_second_reading():
    """Two implementations of one reading is how the form and the model come to disagree
    about the same dataset (D-027)."""
    import inspect as inspect_module

    from mlsandbox import detection

    assert "from_dataset" in inspect_module.getsource(detection.detect)


def test_rows_with_no_outcome_are_dropped_and_counted():
    """They cannot be trained on — there is no answer to learn.

    Nor can they be quietly kept: a file where half the outcomes are blank is a different
    dataset from what its row count claims, and the user should hear that before reading
    anything else about it.
    """
    data = frame(100, label=["a", "b"] * 50)
    data.loc[:49, "label"] = None
    result = detect(data, "label")
    assert isinstance(result, Detected)
    assert result.dropped_rows == 50
    assert result.n_rows == 50


def test_the_missing_rate_describes_the_predictors_not_the_outcome():
    # Gaps in the outcome are a different problem — those rows are gone — and mixing the
    # two would report a rate that describes neither.
    data = frame(100, label=["a", "b"] * 50)
    data.loc[:49, "label"] = None
    result = detect(data, "label")
    assert isinstance(result, Detected)
    assert result.missing_rate == 0.0


def test_a_file_with_no_usable_rows_is_refused():
    data = frame(50, label=[None] * 50)
    assert isinstance(detect(data, "label"), Unpredictable)


# Where the file does not settle the answer


def test_a_small_integer_target_is_flagged_rather_than_guessed():
    """A 1-to-5 rating and a count of children are the same bytes.

    Nothing in the file says which, so the detector says so instead of choosing.
    """
    ratings = np.random.default_rng(0).integers(1, 6, 200)
    result = detect(frame(200, rating=ratings), "rating")
    assert isinstance(result, Detected)
    assert "task" in result.uncertain


def test_a_clear_target_is_not_flagged():
    """A detector that is always unsure is as useless as one that is never unsure."""
    result = detect(frame(200, price=np.linspace(1, 100, 200)), "price")
    assert isinstance(result, Detected)
    assert result.uncertain == []


def test_numeric_columns_holding_codes_are_flagged():
    codes = np.random.default_rng(0).integers(1, 6, 200)
    result = detect(frame(200, code=codes, price=np.linspace(1, 100, 200)), "price")
    assert isinstance(result, Detected)
    assert "feature_types" in result.uncertain


def test_uncertainty_is_named_per_field_never_as_a_whole():
    """"Some of this might be wrong" gives a reader nothing to act on."""
    ratings = np.random.default_rng(0).integers(1, 6, 200)
    result = detect(frame(200, rating=ratings), "rating")
    assert isinstance(result, Detected)
    assert all(isinstance(field, str) for field in result.uncertain)


@pytest.mark.parametrize("column", ["x", "y"])
def test_detection_refuses_before_it_reads(column):
    """The target check runs first, because every other reading depends on it."""
    data = frame(200, **{column: [1.0] * 200})
    assert isinstance(detect(data, column), Unpredictable)
