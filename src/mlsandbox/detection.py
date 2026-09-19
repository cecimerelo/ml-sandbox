"""Reading a dataset's properties from the file, and admitting when it cannot.

Two jobs, and the second is the one that matters. Deriving the meta-features from a frame
is already solved — `metafeatures.from_dataset` does it, and this module must not do it a
second time, because a second implementation is how the form and the model come to
disagree about the same dataset (D-027).

The job here is **judging the reading**. A detector that is always confident is worse than
one that is sometimes wrong, because the user has no way to know which time this is. Two
kinds of doubt are separated:

**The target cannot be predicted at all.** An ID column, a constant, a class with two rows
in it. Silent nonsense is the worst available outcome here: the detector would happily
report "multiclass, 8,000 classes" for an invoice number and train models on it.

**The reading is uncertain.** A column of 0s and 1s stored as numbers might be a category
or might be a measurement, and nothing in the file says which. Flagged for the user rather
than guessed at.
"""

from __future__ import annotations

from typing import Literal

import numpy as np
import pandas as pd

from mlsandbox.base import StrictModel
from mlsandbox.metafeatures import MetaFeatures, from_dataset

MIN_ROWS_PER_CLASS = 10
"""Fewer than this in any class and cross-validation cannot see it in every fold.

Ten rather than the fold count: a class present once per fold is technically splittable and
tells you nothing, and a score computed over two examples is noise wearing a number."""

ID_LIKE_SHARE = 0.95
"""A column whose values are almost all distinct is an identifier, not an outcome.

Not 1.0: a real identifier can repeat once through a duplicated row, and a threshold that
only catches perfect uniqueness misses exactly the messy file this is here to catch."""

AMBIGUOUS_INTEGER_LEVELS = 5
"""Whole numbers with few distinct values might be categories or might be measurements.

A 1-to-5 satisfaction rating and a count of children are the same bytes. The file does not
say which, so neither does the detector.

**Was 10, and it flagged too much.** Bedrooms, bathrooms, cars — ordinary small counts —
almost always fall at or under ten distinct values, so the flag fired on the common case
rather than the ambiguous one. Lowered to 5, which still catches genuine codes (a 1-to-5
rating, a handful of grades) without flagging every small count a house listing has.

There is no threshold in the data that separates the two cleanly — checked against sixty
of the study's own datasets, and the count of columns at each cardinality falls off
smoothly from 3 to 15 with no gap to anchor on. So this is a judgement call, not a discovery,
and it is named here rather than buried in a comparison so the next person who finds it
too tight or too loose knows what to change."""

Problem = Literal["single-value", "identifier", "rare-class", "empty"]


class Unpredictable(StrictModel):
    """Why this column cannot be an outcome, in words naming the column."""

    problem: Problem
    message: str


class Detected(StrictModel):
    """What the file says about itself, and where it is unsure."""

    features: MetaFeatures
    n_rows: int
    n_features: int
    n_classes: int | None = None
    missing_rate: float = 0.0

    dropped_rows: int = 0
    """Rows discarded because the outcome itself was blank.

    They cannot be trained on — there is no answer to learn — and they cannot be quietly
    kept either: a file where a third of the outcomes are missing is a different dataset
    from what its row count claims, and the user should be told before they read anything
    else about it.
    """

    uncertain: list[str] = []
    """Fields the user should check, by name.

    **Per field, never global** (FR-8.2). "Some of this might be wrong" gives a reader
    nothing to act on; naming the field turns a warning into a task.
    """


def inspect_target(frame: pd.DataFrame, column: str) -> Unpredictable | None:
    """Whether this column can be predicted at all.

    Runs before anything is detected, because every other reading depends on the target and
    a nonsense target produces confident nonsense everywhere downstream.
    """
    if column not in frame.columns:
        return Unpredictable(
            problem="empty", message=f"There's no column called `{column}` in this file."
        )

    values = frame[column].dropna()
    if values.empty:
        return Unpredictable(
            problem="empty",
            message=f"Every row is blank in `{column}` — there's nothing to predict.",
        )

    distinct = values.nunique()
    if distinct == 1:
        return Unpredictable(
            problem="single-value",
            message=(
                f"Every row has the same value in `{column}` — there's nothing to predict. "
                "Pick a different column."
            ),
        )

    if distinct / len(values) >= ID_LIKE_SHARE and not _is_continuous(values):
        return Unpredictable(
            problem="identifier",
            message=(
                f"`{column}` has a different value in almost every row. That looks like an "
                "identifier, not something to predict."
            ),
        )

    if is_categorical_target(values):
        counts = values.value_counts()
        smallest = counts.index[-1]
        if counts.iloc[-1] < MIN_ROWS_PER_CLASS:
            return Unpredictable(
                problem="rare-class",
                message=(
                    f"`{smallest}` appears in {counts.iloc[-1]} row"
                    f"{'' if counts.iloc[-1] == 1 else 's'} of `{column}` — too few to test "
                    "a model on. Pick a different column or a coarser target."
                ),
            )

    return None


def detect(frame: pd.DataFrame, column: str) -> Detected | Unpredictable:
    """Read the dataset's properties, given which column is the outcome."""
    unusable = inspect_target(frame, column)
    if unusable is not None:
        return unusable

    # Rows with no outcome are dropped before anything is read. They cannot be trained on,
    # and leaving them in makes every other reading describe a dataset that will not be
    # used — the row count most of all.
    usable = frame.dropna(subset=[column])
    dropped = len(frame) - len(usable)

    target = usable[column]
    features = usable.drop(columns=[column])
    task = "classification" if is_categorical_target(target.dropna()) else "regression"

    return Detected(
        # The same call the study used to describe its own datasets. Not reimplemented:
        # two readings of one file is how the form and the model come to disagree (D-027).
        features=from_dataset(task=task, features=features, target=target.to_numpy()),
        n_rows=len(usable),
        n_features=features.shape[1],
        n_classes=int(target.nunique()) if task == "classification" else None,
        missing_rate=_missing_rate(features),
        uncertain=_uncertain(target, features, task),
        dropped_rows=dropped,
    )


def _uncertain(target: pd.Series, features: pd.DataFrame, task: str) -> list[str]:
    """Which readings the file does not actually settle.

    Named per field so the interface can flag the control rather than the page. A global
    "check this" tells the user to re-read everything, which they will not do.
    """
    doubtful: list[str] = []

    # Whole numbers with few levels: a 1-to-5 rating and a count of children are the same
    # bytes, and the file does not say which one this is.
    values = target.dropna()
    if (
        pd.api.types.is_integer_dtype(values)
        and 2 < values.nunique() <= AMBIGUOUS_INTEGER_LEVELS
    ):
        doubtful.append("task")

    # A numeric column holding a handful of repeated values is a category written as
    # numbers — postcode, product code, grade.
    numeric = features.select_dtypes(include=np.number)
    if any(
        numeric[c].nunique(dropna=True) <= AMBIGUOUS_INTEGER_LEVELS
        and pd.api.types.is_integer_dtype(numeric[c])
        for c in numeric.columns
    ):
        doubtful.append("feature_types")

    return doubtful


def _missing_rate(features: pd.DataFrame) -> float:
    cells = features.shape[0] * features.shape[1]
    return float(features.isna().to_numpy().sum()) / cells if cells else 0.0


def _is_continuous(values: pd.Series) -> bool:
    return pd.api.types.is_float_dtype(values)


def is_categorical_target(values: pd.Series) -> bool:
    """Whether an outcome is a set of categories rather than a number.

    Text is always categories. Numbers are categories only when there are few enough
    distinct values that treating them as an amount would be strange — which is a judgement
    the file cannot make for us, and is why `_uncertain` flags the borderline case rather
    than deciding it quietly.

    Public rather than module-private: `/api/train` (`api.py`) uses the exact same test to
    reject a "regression" task against a column of text before a fit ever starts, rather
    than letting scikit-learn's own `could not convert string to float` reach the user as
    a raw exception message.
    """
    if not pd.api.types.is_numeric_dtype(values):
        return True
    if _is_continuous(values):
        return False
    return values.nunique() <= AMBIGUOUS_INTEGER_LEVELS
