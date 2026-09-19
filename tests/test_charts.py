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


def test_coefficient_plot_carries_every_feature_not_just_a_chart_sized_fold():
    # DESIGN.md's table form for this family is explicitly the full list ("not the
    # top-20 fold"), so the endpoint must not truncate it — only the chart does that,
    # client-side.
    rng = np.random.default_rng(0)
    n = 100
    features = pd.DataFrame({f"x{i}": rng.normal(size=n) for i in range(30)})
    target = sum((i + 1) * features[f"x{i}"] for i in range(30)) + rng.normal(0, 0.01, n)
    pipeline = methods.build("linear_regression", "regression", seed=0)
    pipeline.fit(features, target.to_numpy())

    result = charts.linear_regression_charts(pipeline, features, target.to_numpy())

    assert len(result.coefficients.bars) == 30


def test_leverage_is_between_zero_and_one():
    pipeline, features, target = _fit_linear_regression()

    result = charts.linear_regression_charts(pipeline, features, target)

    for point in result.leverage.points:
        assert 0.0 <= point.leverage <= 1.0 + 1e-9


def _fit_logistic_regression(n_classes: int = 2) -> tuple[object, pd.DataFrame, np.ndarray]:
    rng = np.random.default_rng(0)
    n = 200
    features = pd.DataFrame(
        {
            "size_m2": rng.normal(100, 20, n),
            "bedrooms": rng.integers(1, 5, n),
        }
    )
    score = features["size_m2"] + 10 * features["bedrooms"]
    edges = np.quantile(score, np.linspace(0, 1, n_classes + 1)[1:-1]) if n_classes > 1 else []
    target = np.digitize(score, edges).astype(str)
    pipeline = methods.build("logistic_regression", "classification", seed=0)
    pipeline.fit(features, target)
    return pipeline, features, target


def test_binary_logistic_regression_gets_a_roc_curve_and_coefficients():
    pipeline, features, target = _fit_logistic_regression(n_classes=2)

    result = charts.logistic_regression_charts(pipeline, features, target)

    assert result.roc is not None
    assert 0.0 <= result.roc.auc <= 1.0
    assert result.roc.positive_class == "1"
    assert len(result.coefficients.bars) == 2


def test_binary_confusion_matrix_matches_the_two_classes():
    pipeline, features, target = _fit_logistic_regression(n_classes=2)

    result = charts.logistic_regression_charts(pipeline, features, target)

    assert result.confusion_matrix.labels == ["0", "1"]
    assert len(result.confusion_matrix.matrix) == 2
    assert sum(sum(row) for row in result.confusion_matrix.matrix) == len(features)


def test_multiclass_logistic_regression_has_no_roc_or_coefficients_but_has_a_confusion_matrix():
    pipeline, features, target = _fit_logistic_regression(n_classes=3)

    result = charts.logistic_regression_charts(pipeline, features, target)

    assert result.roc is None
    assert result.coefficients.bars == []
    assert result.confusion_matrix.labels == ["0", "1", "2"]
    assert len(result.confusion_matrix.matrix) == 3


def _fit_discriminant(
    method: str, n_classes: int = 2, n: int = 200
) -> tuple[object, pd.DataFrame, np.ndarray]:
    rng = np.random.default_rng(0)
    features = pd.DataFrame(
        {
            "size_m2": rng.normal(100, 20, n),
            "bedrooms": rng.integers(1, 5, n).astype(float),
            # Pure noise, unrelated to the target — the pair-selection test asserts
            # this one is never picked over the two informative columns.
            "noise": rng.normal(0, 1, n),
        }
    )
    score = features["size_m2"] + 10 * features["bedrooms"]
    edges = np.quantile(score, np.linspace(0, 1, n_classes + 1)[1:-1]) if n_classes > 1 else []
    target = np.digitize(score, edges).astype(str)
    pipeline = methods.build(method, "classification", seed=0)
    pipeline.fit(features, target)
    return pipeline, features, target


def test_lda_boundary_picks_the_two_most_informative_numeric_features():
    pipeline, features, target = _fit_discriminant("lda", n_classes=2)

    result = charts.discriminant_charts(pipeline, features, target)

    assert {result.boundary.feature_x, result.boundary.feature_y} == {"size_m2", "bedrooms"}
    assert "noise" not in {result.boundary.feature_x, result.boundary.feature_y}


def test_qda_boundary_grid_has_the_expected_resolution():
    pipeline, features, target = _fit_discriminant("qda", n_classes=2)

    result = charts.discriminant_charts(pipeline, features, target)

    assert len(result.boundary.grid) == charts.BOUNDARY_GRID_RESOLUTION**2
    assert len(result.boundary.points) == len(features)
    assert result.boundary.too_many_classes is False


def test_confusion_matrix_and_boundary_report_the_same_classes():
    pipeline, features, target = _fit_discriminant("lda", n_classes=3)

    result = charts.discriminant_charts(pipeline, features, target)

    assert result.confusion_matrix.labels == result.boundary.classes == ["0", "1", "2"]


def test_a_caller_can_override_the_auto_selected_feature_pair():
    pipeline, features, target = _fit_discriminant("lda", n_classes=2)

    result = charts.discriminant_charts(
        pipeline, features, target, feature_x="noise", feature_y="bedrooms"
    )

    assert (result.boundary.feature_x, result.boundary.feature_y) == ("noise", "bedrooms")
    assert len(result.boundary.grid) == charts.BOUNDARY_GRID_RESOLUTION**2


def test_an_invalid_override_falls_back_to_auto_selection():
    pipeline, features, target = _fit_discriminant("lda", n_classes=2)

    result = charts.discriminant_charts(
        pipeline, features, target, feature_x="not_a_column", feature_y="bedrooms"
    )

    assert {result.boundary.feature_x, result.boundary.feature_y} == {"size_m2", "bedrooms"}


def test_more_than_the_class_cap_has_no_grid_but_still_has_a_confusion_matrix():
    pipeline, features, target = _fit_discriminant("lda", n_classes=7, n=700)

    result = charts.discriminant_charts(pipeline, features, target)

    assert result.boundary.too_many_classes is True
    assert result.boundary.grid == []
    assert result.boundary.points == []
    assert len(result.confusion_matrix.labels) == 7


def test_fewer_than_two_numeric_columns_has_no_grid():
    rng = np.random.default_rng(0)
    n = 200
    features = pd.DataFrame({"city": rng.choice(["Madrid", "Sevilla"], n)})
    target = rng.choice(["yes", "no"], n)
    pipeline = methods.build("lda", "classification", seed=0)
    pipeline.fit(features, target)

    result = charts.discriminant_charts(pipeline, features, target)

    assert result.boundary.grid == []
    assert result.boundary.numeric_features == []


def _fit_knn(
    task: str = "classification", n_classes: int = 2
) -> tuple[object, pd.DataFrame, np.ndarray]:
    rng = np.random.default_rng(0)
    n = 200
    features = pd.DataFrame(
        {
            "size_m2": rng.normal(100, 20, n),
            "bedrooms": rng.integers(1, 5, n).astype(float),
        }
    )
    score = features["size_m2"] + 10 * features["bedrooms"]
    if task == "regression":
        target = score.to_numpy() + rng.normal(0, 5, n)
    else:
        edges = np.quantile(score, np.linspace(0, 1, n_classes + 1)[1:-1]) if n_classes > 1 else []
        target = np.digitize(score, edges).astype(str)
    pipeline = methods.build("knn", task, seed=0)
    pipeline.fit(features, target)
    return pipeline, features, target


def test_knn_tuning_curve_has_a_point_per_grid_value_and_names_the_chosen_k():
    pipeline, features, target = _fit_knn()

    result = charts.knn_charts(pipeline, features, target)

    model = pipeline.named_steps["model"]
    assert len(result.tuning.points) == len(model.cv_results_["param_n_neighbors"])
    assert result.tuning.chosen_k == model.best_params_["n_neighbors"]
    assert result.tuning.chosen_k in [p.k for p in result.tuning.points]


def test_knn_classification_gets_a_boundary_too():
    pipeline, features, target = _fit_knn()

    result = charts.knn_charts(pipeline, features, target)

    assert result.boundary.too_many_classes is False
    assert len(result.boundary.grid) == charts.BOUNDARY_GRID_RESOLUTION**2
    assert result.boundary.classes == ["0", "1"]


def test_knn_regression_has_a_tuning_curve_but_no_meaningful_boundary():
    pipeline, features, target = _fit_knn(task="regression")

    result = charts.knn_charts(pipeline, features, target)

    assert len(result.tuning.points) > 0
    # A continuous target has far more than MAX_BOUNDARY_CLASSES distinct values, so
    # the shared boundary helper reports it the same way it reports any other
    # too-many-classes case, rather than a boundary fragmented into one region per row.
    assert result.boundary.too_many_classes is True
    assert result.boundary.grid == []


def test_knn_has_no_confusion_matrix_field():
    # FR-4.2 lists only a decision boundary and an accuracy-vs-K curve for KNN — no
    # confusion matrix, unlike Logistic Regression or Naive Bayes.
    assert "confusion_matrix" not in charts.KnnCharts.model_fields
