"""Chart data computed straight from a fitted pipeline (#83, FR-4.2) — no HTTP layer."""

from __future__ import annotations

import numpy as np
import pandas as pd

from mlsandbox import charts, methods


def _fit_linear_regression() -> tuple[object, pd.DataFrame, np.ndarray]:
    rng = np.random.default_rng(0)
    n = 200
    features = pd.DataFrame(
        {
            "size_m2": rng.normal(100, 20, n),
            "bedrooms": rng.integers(1, 5, n),
            "city": rng.choice(["Madrid", "Barcelona"], n),
        }
    )
    target = 1000 * features["size_m2"] + 5000 * features["bedrooms"] + rng.normal(0, 100, n)
    pipeline = methods.build("linear_regression", "regression", seed=0)
    pipeline.fit(features, target.to_numpy())
    return pipeline, features, target.to_numpy()


def test_a_near_perfect_fit_has_tiny_residuals_and_a_high_r2():
    pipeline, features, target = _fit_linear_regression()

    result = charts.linear_regression_charts(pipeline, features, target)

    assert result.predicted_vs_actual.r2 > 0.99
    assert all(abs(p.y) < 500 for p in result.residual.points)


def test_every_row_gets_one_point_in_each_per_row_chart():
    pipeline, features, target = _fit_linear_regression()

    result = charts.linear_regression_charts(pipeline, features, target)

    assert len(result.residual.points) == len(features)
    assert len(result.predicted_vs_actual.points) == len(features)
    assert len(result.leverage.points) == len(features)


def test_coefficients_are_sorted_by_magnitude_descending():
    pipeline, features, target = _fit_linear_regression()

    result = charts.linear_regression_charts(pipeline, features, target)

    magnitudes = [abs(bar.value) for bar in result.coefficients.bars]
    assert magnitudes == sorted(magnitudes, reverse=True)
    # One-hot("city") + size_m2 + bedrooms: fewer than the top-20 fold, so nothing drops.
    assert len(result.coefficients.bars) == result.coefficients.total_features


def test_coefficient_plot_folds_past_the_top_20():
    rng = np.random.default_rng(0)
    n = 100
    features = pd.DataFrame({f"x{i}": rng.normal(size=n) for i in range(30)})
    target = sum((i + 1) * features[f"x{i}"] for i in range(30)) + rng.normal(0, 0.01, n)
    pipeline = methods.build("linear_regression", "regression", seed=0)
    pipeline.fit(features, target.to_numpy())

    result = charts.linear_regression_charts(pipeline, features, target.to_numpy())

    assert len(result.coefficients.bars) == charts.COEFFICIENT_TOP_N
    assert result.coefficients.total_features == 30


def test_leverage_is_between_zero_and_one():
    pipeline, features, target = _fit_linear_regression()

    result = charts.linear_regression_charts(pipeline, features, target)

    for point in result.leverage.points:
        assert 0.0 <= point.leverage <= 1.0 + 1e-9
