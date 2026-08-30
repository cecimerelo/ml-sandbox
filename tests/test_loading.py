"""Which column is the outcome — and why guessing at it is not allowed.

The bug these tests exist for: `split_target` used to fall back to the last column when
no column was named `target`, on the belief that OpenML puts the outcome last. It does
not. Five of the forty OpenML datasets declare it elsewhere, so `kings_county` was trained
to predict the day of the month from the house's price, and scored R² between 0.00 and
0.04 for every method — which reads as a hard dataset, not as a bug.
"""

import pandas as pd
import pytest

from mlsandbox.loading import TARGET_COLUMN, split_target


def frame(**columns) -> pd.DataFrame:
    return pd.DataFrame(columns)


def test_splits_on_the_named_column():
    features, target = split_target(frame(a=[1, 2], target=[3, 4], b=[5, 6]))
    assert list(features.columns) == ["a", "b"]
    assert list(target) == [3, 4]


def test_the_target_is_not_the_last_column_by_default():
    """The heart of it. A frame whose outcome sits in the middle must still split there."""
    _, target = split_target(frame(price=[1, 2], target=[9, 9], date_day=[3, 4]))
    assert list(target) == [9, 9]


def test_a_frame_with_no_named_target_raises():
    """Rather than guessing.

    A guess that is usually right is worse than an error here: nothing downstream can tell
    a wrongly-chosen target from a genuinely difficult problem, so the study reports the
    second when it has the first.
    """
    with pytest.raises(ValueError, match=TARGET_COLUMN):
        split_target(frame(a=[1, 2], b=[3, 4]))


def test_the_error_says_whose_job_it_is():
    with pytest.raises(ValueError, match="loader is responsible"):
        split_target(frame(a=[1]))


def test_the_target_is_removed_from_the_predictors():
    features, _ = split_target(frame(target=[1, 2], a=[3, 4]))
    assert TARGET_COLUMN not in features.columns
