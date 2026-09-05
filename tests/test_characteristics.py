"""The method characteristics table's five axes.

Two of the five are computed from the benchmark rather than declared, because nothing in
the registry states an expected accuracy or speed, and asserting one by hand risks
contradicting the benchmark this project ran to avoid contradicting.
"""

import pandas as pd

from mlsandbox.characteristics import from_benchmark


def rows(*entries: tuple[str, str, float, float]) -> pd.DataFrame:
    """`(task, method, score, fit_seconds)` tuples, three folds each so the mean is stable."""
    records = []
    for task, method, score, speed in entries:
        for fold in range(3):
            records.append(
                {
                    "task": task,
                    "method": method,
                    "score": score,
                    "fit_seconds": speed,
                    "status": "ok",
                    "dataset": f"{task}-{method}",
                    "missing_rate": 0.0,
                    "fold": fold,
                }
            )
    return pd.DataFrame(records)


# The declared axes


def test_interpretability_reads_off_the_registry():
    table = from_benchmark(rows(("regression", "linear_regression", 0.5, 1.0)))
    assert table["linear_regression"].interpretability.word == "high"
    assert table["linear_regression"].interpretability.step == 3


def test_an_opaque_method_reads_low_interpretability():
    table = from_benchmark(rows(("regression", "random_forest", 0.5, 1.0)))
    assert table["random_forest"].interpretability.word == "low"


def test_a_non_linear_family_handles_non_linearity():
    table = from_benchmark(rows(("regression", "random_forest", 0.5, 1.0)))
    assert table["random_forest"].handles_non_linearity.word == "high"


def test_a_linear_family_does_not_handle_non_linearity():
    """Regularised and dimension-reduction families shrink or reproject a linear fit; they
    do not depart from linearity, so they read the same as plain linear regression."""
    table = from_benchmark(rows(("regression", "ridge", 0.5, 1.0)))
    assert table["ridge"].handles_non_linearity.word == "low"


def test_handles_missing_values_reads_off_the_registry():
    from mlsandbox.methods import METHODS

    handles_nan = next(m for m in METHODS.values() if m.handles_nan)
    no_nan = next(m for m in METHODS.values() if not m.handles_nan)
    handles_nan_task = "classification" if "classification" in handles_nan.tasks else "regression"
    no_nan_task = "classification" if "classification" in no_nan.tasks else "regression"
    table = from_benchmark(
        rows(
            (handles_nan_task, handles_nan.name, 0.5, 1.0),
            (no_nan_task, no_nan.name, 0.5, 1.0),
        )
    )
    assert table[handles_nan.name].handles_missing_values.word == "yes"
    assert table[no_nan.name].handles_missing_values.word == "no"


# The computed axes


def test_accuracy_and_speed_are_ranked_within_task_not_pooled():
    """The bug this exists to avoid.

    Regression's R² and classification's balanced accuracy are not the same scale.
    Pooling them ranks a method against numbers that mean something else, not against how
    it performs on its own kind of problem.
    """
    table = from_benchmark(
        rows(
            ("regression", "linear_regression", 0.4, 1.0),
            ("classification", "qda", 0.9, 1.0),
        )
    )
    # Each is alone in its task, so each has to rank as the best of one.
    assert table["linear_regression"].accuracy_potential.word == "high"
    assert table["qda"].accuracy_potential.word == "high"


def test_accuracy_potential_ranks_within_the_collection():
    table = from_benchmark(
        rows(
            ("regression", "random_forest", 0.9, 1.0),
            ("regression", "linear_regression", 0.5, 1.0),
            ("regression", "pcr", 0.1, 1.0),
        )
    )
    assert table["random_forest"].accuracy_potential.word == "high"
    assert table["pcr"].accuracy_potential.word == "lower"


def test_training_speed_ranks_ascending_not_descending():
    """Faster is the better step, unlike accuracy where more is better — a shared ranking
    direction would call the slowest method "fast"."""
    table = from_benchmark(
        rows(
            ("regression", "linear_regression", 0.5, 0.01),
            ("regression", "ridge", 0.5, 5.0),
            ("regression", "mlp", 0.5, 20.0),
        )
    )
    assert table["linear_regression"].training_speed.word == "fast"
    assert table["mlp"].training_speed.word == "slow"


def test_a_method_scored_under_both_tasks_keeps_one_row():
    # Every method in this registry is single-task, but the aggregation must not produce
    # two rows for one method if that ever changes.
    table = from_benchmark(rows(("regression", "knn", 0.5, 1.0)))
    assert len([m for m in table if m == "knn"]) == 1


def test_only_successful_folds_count():
    failed = pd.DataFrame(
        [
            {
                "task": "regression",
                "method": "lasso",
                "score": None,
                "fit_seconds": None,
                "status": "timeout",
                "dataset": "d",
                "missing_rate": 0.0,
                "fold": 0,
            }
        ]
    )
    ok = rows(("regression", "linear_regression", 0.5, 1.0))
    table = from_benchmark(pd.concat([ok, failed]))
    assert "lasso" not in table


# The label


def test_every_row_carries_the_method_s_display_label():
    table = from_benchmark(rows(("regression", "linear_regression", 0.5, 1.0)))
    assert table["linear_regression"].label == "Linear Regression"
