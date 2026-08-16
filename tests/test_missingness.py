"""Injected missingness.

The target-never-touched rule and the reproducibility of the injection are the two
properties the experiment rests on: break either and the comparison across rates stops
meaning anything.
"""

import numpy as np
import pandas as pd
import pytest

from mlsandbox.missingness import inject_missing, missing_rate


def build_frame(target: list) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "a": range(100),
            "b": range(100, 200),
            "c": range(200, 300),
            "target": target,
        }
    )


CLASSIFICATION_TARGET = [0, 1] * 50
REGRESSION_TARGET = [i * 1.5 for i in range(100)]


@pytest.fixture
def frame() -> pd.DataFrame:
    return build_frame(CLASSIFICATION_TARGET)


@pytest.fixture(params=["classification", "regression"])
def any_task_frame(request) -> pd.DataFrame:
    targets = {
        "classification": CLASSIFICATION_TARGET,
        "regression": REGRESSION_TARGET,
    }
    return build_frame(targets[request.param])


def test_never_touches_the_target_whatever_the_task(any_task_frame):
    # Task-agnostic on purpose: a blanked label and a blanked continuous outcome are the
    # same mistake. Either removes what is being predicted rather than making it harder
    # to predict, and silently shrinks the effective sample.
    result = inject_missing(any_task_frame, rate=0.5, seed=1)
    assert result["target"].isna().sum() == 0


def test_predictors_lose_exactly_the_requested_share(any_task_frame):
    result = inject_missing(any_task_frame, rate=0.25, seed=1)
    assert missing_rate(result) == pytest.approx(0.25)


def test_achieves_the_requested_rate_exactly(frame):
    # Sampling positions without replacement, rather than drawing independently per cell,
    # is what makes the achieved rate exact instead of approximate.
    result = inject_missing(frame, rate=0.25, seed=1)
    assert missing_rate(result) == pytest.approx(0.25)


def test_same_seed_gives_the_same_gaps(frame):
    first = inject_missing(frame, rate=0.2, seed=7)
    second = inject_missing(frame, rate=0.2, seed=7)
    assert first.isna().equals(second.isna())


def test_different_seeds_give_different_gaps(frame):
    first = inject_missing(frame, rate=0.2, seed=1)
    second = inject_missing(frame, rate=0.2, seed=2)
    assert not first.isna().equals(second.isna())


def test_leaves_the_input_untouched(frame):
    inject_missing(frame, rate=0.5, seed=1)
    assert frame.isna().sum().sum() == 0


def test_zero_rate_is_a_no_op(frame):
    assert inject_missing(frame, rate=0.0, seed=1).equals(frame)


def test_rejects_a_rate_of_one_or_more(frame):
    # A rate of 1 would blank every predictor, leaving nothing to learn from.
    with pytest.raises(ValueError):
        inject_missing(frame, rate=1.0, seed=1)


def test_integer_columns_become_float_so_they_can_hold_nan(frame):
    result = inject_missing(frame, rate=0.1, seed=1)
    assert result["a"].dtype == np.float64


def test_a_frame_with_only_a_target_is_returned_unchanged():
    only_target = pd.DataFrame({"target": [0, 1, 0]})
    assert inject_missing(only_target, rate=0.5, seed=1).equals(only_target)


def test_missing_rate_reads_back_what_was_injected(frame):
    for rate in (0.05, 0.25, 0.4):
        result = inject_missing(frame, rate=rate, seed=3)
        assert missing_rate(result) == pytest.approx(rate)
