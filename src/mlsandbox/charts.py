"""Per-method chart data (FR-4.2, #83), computed from an already-fitted pipeline.

Nothing here fits a model — `TrainingJob.results[method].fitted` (D-053) is the pipeline
this reads from, the same object `/api/train` produced. The dataset comes in fresh on
every call (FR-7.2: re-sent by the frontend, never retained past the request, same
promise `eda.py` already makes for the upload/detect/EDA paths) and is used only to
compute predictions/residuals against that pipeline — never to refit it, so the chart a
user sees is guaranteed to be the same model the training panel scored, not a second fit
that could disagree with it.

Table forms (DESIGN.md's "Table-view form, per family") are the frontend's job: it
already has the same points this module returns and can reduce them to summary
statistics or a feature×value list without another round trip.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.metrics import auc, confusion_matrix, r2_score, roc_curve
from sklearn.pipeline import Pipeline

from mlsandbox.base import StrictModel


class ScatterPoint(StrictModel):
    x: float
    y: float


class ResidualPlot(StrictModel):
    """Residual vs. fitted (DESIGN.md's "Fit / residual" family): x is the prediction,
    y is actual minus predicted, with the family's dashed y = 0 reference line drawn
    client-side, not shipped as data."""

    points: list[ScatterPoint]


class PredictedVsActual(StrictModel):
    """x is the true value, y is the prediction, with the family's dashed y = x
    reference line drawn client-side. `r2` is the "fit statistic" DESIGN.md's table
    form for this family names alongside n/mean/SD/min/max."""

    points: list[ScatterPoint]
    r2: float


class CoefficientBar(StrictModel):
    feature: str
    value: float


class CoefficientPlot(StrictModel):
    """Every coefficient, sorted by |value| descending — DESIGN.md's "Coefficients /
    importance" family caps the *chart* at the top `COEFFICIENT_TOP_N`, but its table
    form is explicitly the full list ("not the top-20 fold — this is where the other
    480 live"). Sending everything here and letting the chart slice its own top N is
    what makes both true from one field, rather than needing two."""

    bars: list[CoefficientBar]


class LeveragePoint(StrictModel):
    leverage: float
    studentized_residual: float


class LeveragePlot(StrictModel):
    """Cook's-distance-style diagnostic: each row's influence (leverage, the diagonal
    of the hat matrix) against how far its residual is once scaled for that influence
    (the studentized residual) — the pair FR-4.2 added alongside the residual plot to
    flag points that pull the fit disproportionately."""

    points: list[LeveragePoint]


class LinearRegressionCharts(StrictModel):
    residual: ResidualPlot
    predicted_vs_actual: PredictedVsActual
    coefficients: CoefficientPlot
    leverage: LeveragePlot


class RocPoint(StrictModel):
    false_positive_rate: float
    true_positive_rate: float


class RocCurve(StrictModel):
    """`positive_class` is whichever of the two classes scikit-learn's `classes_`
    lists second — an arbitrary but consistent choice (nothing in the uploaded data
    says which outcome is "positive"), stated here so the chart can label it rather
    than silently picking one."""

    points: list[RocPoint]
    auc: float
    positive_class: str


class ConfusionMatrix(StrictModel):
    """`matrix[i][j]` is how many rows whose actual class was `labels[i]` the model
    predicted as `labels[j]` — the order `classes_` already fixed, not sorted twice."""

    labels: list[str]
    matrix: list[list[int]]


class LogisticRegressionCharts(StrictModel):
    """`roc` is `None`, and `coefficients.bars` is empty, for a target with more than
    two classes: FR-4.2's ROC curve, like ISLR's own treatment of it, is a
    binary-classification chart, and a multiclass `coef_` has one row per class rather
    than the single signed value per feature this chart plots. A multiclass target
    still gets its confusion matrix, which scales to any class count."""

    roc: RocCurve | None
    confusion_matrix: ConfusionMatrix
    coefficients: CoefficientPlot


def _design_matrix(pipeline: Pipeline, features: pd.DataFrame) -> np.ndarray:
    """The matrix `model` actually saw, intercept column included.

    `prepare`'s output, not `features` itself: leverage and coefficients are only
    meaningful in the space the model was fit in (imputed, encoded, scaled), the same
    reason the coefficient plot reads feature names from `prepare.get_feature_names_out()`
    rather than from `features.columns`.
    """
    transformed = np.asarray(pipeline.named_steps["prepare"].transform(features))
    return np.column_stack([np.ones(len(transformed)), transformed])


def _leverage(design: np.ndarray) -> np.ndarray:
    """The hat matrix's diagonal, `h_ii = x_i (X'X)^+ x_i`, computed per row rather
    than forming the full n×n hat matrix — the same numbers, without the O(n²) memory
    a large upload would otherwise cost."""
    gram_pinv = np.linalg.pinv(design.T @ design)
    return np.einsum("ij,jk,ik->i", design, gram_pinv, design)


def _coefficient_plot(pipeline: Pipeline) -> CoefficientPlot:
    """`model.coef_` flattened, feature names read from `prepare` — meaningful only
    when `coef_` is a single row (linear regression, or binary logistic regression's
    one row of log-odds), not a multiclass classifier's one-row-per-class matrix."""
    prepare = pipeline.named_steps["prepare"]
    model = pipeline.named_steps["model"]
    feature_names = list(prepare.get_feature_names_out())
    coefficients = np.asarray(model.coef_).ravel()
    order = np.argsort(-np.abs(coefficients))
    bars = [CoefficientBar(feature=feature_names[i], value=float(coefficients[i])) for i in order]
    return CoefficientPlot(bars=bars)


def linear_regression_charts(
    pipeline: Pipeline, features: pd.DataFrame, target: np.ndarray
) -> LinearRegressionCharts:
    predictions = pipeline.predict(features)
    residuals = target - predictions
    coefficients = _coefficient_plot(pipeline)

    design = _design_matrix(pipeline, features)
    leverage = _leverage(design)
    degrees_of_freedom = max(len(design) - design.shape[1], 1)
    residual_std_error = float(np.sqrt(np.sum(residuals**2) / degrees_of_freedom))
    # A leverage of 1 makes a row's studentized residual undefined (it predicts its own
    # value exactly); floored rather than excluded, so one such row does not drop the
    # point from the plot entirely.
    denominator = np.sqrt(np.maximum(1.0 - leverage, 1e-6))
    studentized = (
        residuals / (residual_std_error * denominator)
        if residual_std_error > 0
        else np.zeros_like(residuals)
    )

    return LinearRegressionCharts(
        residual=ResidualPlot(
            points=[
                ScatterPoint(x=float(p), y=float(r))
                for p, r in zip(predictions, residuals, strict=True)
            ]
        ),
        predicted_vs_actual=PredictedVsActual(
            points=[
                ScatterPoint(x=float(a), y=float(p))
                for a, p in zip(target, predictions, strict=True)
            ],
            r2=float(r2_score(target, predictions)),
        ),
        coefficients=coefficients,
        leverage=LeveragePlot(
            points=[
                LeveragePoint(leverage=float(h), studentized_residual=float(s))
                for h, s in zip(leverage, studentized, strict=True)
            ]
        ),
    )


def logistic_regression_charts(
    pipeline: Pipeline, features: pd.DataFrame, target: np.ndarray
) -> LogisticRegressionCharts:
    model = pipeline.named_steps["model"]
    classes = [str(c) for c in model.classes_]
    predictions = pipeline.predict(features)

    matrix = confusion_matrix(target, predictions, labels=model.classes_)

    roc: RocCurve | None = None
    if len(classes) == 2:
        positive_class = model.classes_[1]
        probabilities = pipeline.predict_proba(features)[:, 1]
        false_positive_rate, true_positive_rate, _ = roc_curve(
            target, probabilities, pos_label=positive_class
        )
        roc = RocCurve(
            points=[
                RocPoint(false_positive_rate=float(f), true_positive_rate=float(t))
                for f, t in zip(false_positive_rate, true_positive_rate, strict=True)
            ],
            auc=float(auc(false_positive_rate, true_positive_rate)),
            positive_class=str(positive_class),
        )

    return LogisticRegressionCharts(
        roc=roc,
        confusion_matrix=ConfusionMatrix(labels=classes, matrix=matrix.tolist()),
        # A multiclass `coef_` has one row per class — plotting it as one signed bar
        # per feature would silently mix rows that mean different things.
        coefficients=_coefficient_plot(pipeline) if len(classes) == 2 else CoefficientPlot(bars=[]),
    )
