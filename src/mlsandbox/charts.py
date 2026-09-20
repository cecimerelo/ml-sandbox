"""Per-method chart data (FR-4.2, #83), computed from an already-fitted pipeline.

`TrainingJob.results[method].fitted` (D-053) — the pipeline `/api/train` already
produced — is never refit to change what it predicts: every chart's residuals,
predictions, and decision regions come from that one fitted model, so what a user sees
here is guaranteed to agree with what the training panel scored. The dataset comes in
fresh on every call (FR-7.2: re-sent by the frontend, never retained between requests,
the same promise `eda.py` makes for the upload/detect/EDA paths).

**One family is a deliberate exception.** Ridge/Lasso's coefficient-shrinkage path
(#100) is about the hyperparameter landscape the fit lives in, not the fit's own
predictions — no sklearn `*CV` object retains a coefficient trajectory across every
alpha it tried, only the one it chose. Drawing that path means fitting one plain
`Ridge`/`Lasso`/`LogisticRegression` per candidate already in that same `*CV`'s own
grid — never a new grid, never a value the original tuning didn't already consider — so
the chosen point on the path still matches the pipeline exactly.

Table forms (DESIGN.md's "Table-view form, per family") are the frontend's job: it
already has the same points this module returns and can reduce them to summary
statistics or a feature×value list without another round trip.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.feature_selection import f_classif
from sklearn.linear_model import (
    Lasso,
    LogisticRegression,
    LogisticRegressionCV,
    Ridge,
    RidgeCV,
)
from sklearn.metrics import auc, confusion_matrix, r2_score, roc_curve
from sklearn.model_selection import cross_val_score
from sklearn.pipeline import Pipeline

from mlsandbox.base import StrictModel

BOUNDARY_GRID_RESOLUTION = 40
"""Cells per axis for a decision-boundary grid — 1,600 cells, fine enough to read the
shape of a region without the payload scaling with the dataset's own row count."""

MAX_BOUNDARY_CLASSES = 6
"""DESIGN.md's "Boundaries" family: above this, a boundary plot is not rendered at
all — a plot needing that many distinguishable regions is not a visualization."""


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


class BoundaryCell(StrictModel):
    """One point on the decision-boundary grid — `predicted_class` is what the pipeline
    predicts with `feature_x`/`feature_y` at `(x, y)` and every other feature held at a
    representative value (mean for a numeric column, mode for a categorical one)."""

    x: float
    y: float
    predicted_class: str


class BoundaryPoint(StrictModel):
    """One real row, projected onto `feature_x`/`feature_y` — plotted over the grid so
    the boundary can be read against the data it was actually fit on."""

    x: float
    y: float
    actual_class: str


class DecisionBoundary(StrictModel):
    """FR-4.3: the system auto-selects `feature_x`/`feature_y` (by ANOVA F-score, the
    two numeric columns that individually separate the classes best) unless the caller
    names its own pair — the mechanism FR-4.3's "the user can swap the selected
    features" needs. `grid` and `points` are both empty when there aren't two numeric
    columns to plot, or when `classes` has more than `MAX_BOUNDARY_CLASSES` — a boundary
    over that many regions is not a visualization DESIGN.md asks for, not a bug here.
    """

    feature_x: str
    feature_y: str
    numeric_features: list[str]
    """Every numeric column — what a "swap the selected features" control chooses
    between. Always includes `feature_x`/`feature_y` themselves."""
    classes: list[str]
    grid: list[BoundaryCell]
    points: list[BoundaryPoint]
    too_many_classes: bool
    looks_continuous: bool
    """`too_many_classes` alone doesn't say why: a genuinely categorical column with,
    say, 12 rare categories reads very differently from a column that is actually
    continuous (price, an ID) and so has nearly as many "classes" as rows — the second
    means the wrong kind of column was used as a classification target at all, not
    just too many categories to plot. `True` when classes outnumber half the rows."""


class DiscriminantCharts(StrictModel):
    """LDA and QDA's fixed set (FR-4.2): a decision boundary and a confusion matrix.
    Shared by both — neither method has a coefficient plot LDA/QDA's own kind of
    boundary is drawn from (QDA has no single coefficient at all; LDA's only reduces
    cleanly to one for the binary case), so unlike Logistic Regression there is no
    third chart to fall back to when the boundary itself can't be shown."""

    boundary: DecisionBoundary
    confusion_matrix: ConfusionMatrix


class TuningPoint(StrictModel):
    k: int
    score: float


class TuningCurve(StrictModel):
    """DESIGN.md's "Tuning curves" family: accuracy (or, for a regression KNN, the
    study's own r2) at every `k` the internal grid search actually tried — read
    straight from the already-fitted `GridSearchCV.cv_results_`, never a second round
    of cross-validation just to draw a chart."""

    points: list[TuningPoint]
    chosen_k: int
    """The value `GridSearchCV` actually picked — DESIGN.md's "chosen optimum gets a
    filled dot plus a direct label" needs to know which point that is."""


class KnnCharts(StrictModel):
    """KNN's fixed set (FR-4.2): a decision boundary and its accuracy-vs-K curve. No
    confusion matrix — FR-4.2 doesn't list one for this method, unlike Logistic
    Regression or Naive Bayes."""

    boundary: DecisionBoundary
    tuning: TuningCurve


class NaiveBayesCharts(StrictModel):
    """Confusion matrix, ROC curve — FR-4.2. No coefficient plot: `GaussianNB` stores
    each class's per-feature mean and variance, not the single signed weight per
    feature a coefficient plot draws, so unlike Logistic Regression there is nothing
    third to fall back to."""

    roc: RocCurve | None
    confusion_matrix: ConfusionMatrix


class RegularizationPoint(StrictModel):
    x: float
    score: float


class RegularizationCurve(StrictModel):
    """DESIGN.md's "Tuning curves" family, generalised past KNN's integer K to a
    continuous regularization strength. `score` is always the same bounded,
    higher-is-better metric regardless of which estimator produced the curve — see
    `_regression_shrinkage`'s own docstring for why neither `RidgeCV` nor `LassoCV`'s
    own stored curve can be reused as-is here."""

    points: list[RegularizationPoint]
    chosen_x: float
    x_label: str
    """The estimator's own parameter name — "α" for Ridge/Lasso, "C" for the
    `LogisticRegressionCV` classification uses. Not converted to a single "λ": `C` is
    the inverse of a regularization strength, and forcing that conversion risks a sign
    error for a labelling choice alone."""


class ShrinkagePoint(StrictModel):
    feature: str
    x: float
    coefficient: float


class ShrinkagePath(StrictModel):
    """DESIGN.md's "Shrinkage paths" family: every feature's coefficient at every
    regularization strength `RegularizationCurve` plots. `promoted_features` are the
    top 3 by |coefficient| at the chosen strength — DESIGN.md's stated exception to
    "do not generate hues" for this one family, direct-labelled instead of coloured
    like every other line chart. Empty for a multiclass classification Ridge/Lasso:
    `coef_` there has one row per class, the same reason Logistic Regression's own
    coefficient plot is empty for a multiclass target."""

    points: list[ShrinkagePoint]
    promoted_features: list[str]
    x_label: str


class ShrinkageCharts(StrictModel):
    """Ridge and Lasso's fixed set (FR-4.2): a coefficient shrinkage path and a
    CV-error/score-vs-regularization curve. Shared by both, and by their
    classification counterparts (`LogisticRegressionCV` with `l1_ratios=(0.0,)` or
    `(1.0,)`) — the two differ only in which sklearn `*CV` class this reads."""

    shrinkage: ShrinkagePath
    tuning: RegularizationCurve


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
    pipeline: Pipeline, features: pd.DataFrame, target: np.ndarray, **_unused: object
) -> LinearRegressionCharts:
    """`**_unused` swallows `feature_x`/`feature_y` — every `CHART_BUILDERS` entry gets
    called with them (FR-4.3's decision-boundary override), even the ones with no
    boundary to place them on."""
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


def _roc_curve(
    pipeline: Pipeline, features: pd.DataFrame, target: np.ndarray, classes: np.ndarray
) -> RocCurve | None:
    """`None` for anything but a two-class target — FR-4.2's ROC curve, like ISLR's own
    treatment of it, only means something for binary classification. `positive_class`
    is whichever of the two `classes_` lists second: an arbitrary but consistent
    choice, since nothing in the uploaded data says which outcome is "positive"."""
    if len(classes) != 2:
        return None
    positive_class = classes[1]
    probabilities = pipeline.predict_proba(features)[:, 1]
    false_positive_rate, true_positive_rate, _ = roc_curve(
        target, probabilities, pos_label=positive_class
    )
    return RocCurve(
        points=[
            RocPoint(false_positive_rate=float(f), true_positive_rate=float(t))
            for f, t in zip(false_positive_rate, true_positive_rate, strict=True)
        ],
        auc=float(auc(false_positive_rate, true_positive_rate)),
        positive_class=str(positive_class),
    )


def logistic_regression_charts(
    pipeline: Pipeline, features: pd.DataFrame, target: np.ndarray, **_unused: object
) -> LogisticRegressionCharts:
    """`**_unused`: see `linear_regression_charts`."""
    model = pipeline.named_steps["model"]
    classes = [str(c) for c in model.classes_]
    predictions = pipeline.predict(features)
    matrix = confusion_matrix(target, predictions, labels=model.classes_)

    return LogisticRegressionCharts(
        roc=_roc_curve(pipeline, features, target, model.classes_),
        confusion_matrix=ConfusionMatrix(labels=classes, matrix=matrix.tolist()),
        # A multiclass `coef_` has one row per class — plotting it as one signed bar
        # per feature would silently mix rows that mean different things.
        coefficients=_coefficient_plot(pipeline) if len(classes) == 2 else CoefficientPlot(bars=[]),
    )


def naive_bayes_charts(
    pipeline: Pipeline, features: pd.DataFrame, target: np.ndarray, **_unused: object
) -> NaiveBayesCharts:
    """`**_unused`: see `linear_regression_charts`."""
    model = pipeline.named_steps["model"]
    classes = [str(c) for c in model.classes_]
    predictions = pipeline.predict(features)
    matrix = confusion_matrix(target, predictions, labels=model.classes_)

    return NaiveBayesCharts(
        roc=_roc_curve(pipeline, features, target, model.classes_),
        confusion_matrix=ConfusionMatrix(labels=classes, matrix=matrix.tolist()),
    )


def _numeric_columns(features: pd.DataFrame) -> list[str]:
    return [c for c in features.columns if pd.api.types.is_numeric_dtype(features[c])]


def _best_boundary_pair(
    features: pd.DataFrame, target: np.ndarray, numeric: list[str]
) -> tuple[str, str]:
    """The two numeric columns that individually separate the classes best.

    ANOVA F-score, not the model's own coefficients: QDA has no single coefficient at
    all (a quadratic boundary per class), and LDA's only reduces to one cleanly for the
    binary case — a model-agnostic, data-only ranking is the one thing that works
    identically for both, and reads the same way a reader would expect "most important"
    to mean here: which column, alone, tells the classes apart most clearly.
    """
    values = features[numeric].apply(lambda col: col.fillna(col.mean()))
    scores, _ = f_classif(values.to_numpy(), target)
    scores = np.nan_to_num(scores)
    order = np.argsort(-scores)
    return numeric[order[0]], numeric[order[1]]


def _representative_row(features: pd.DataFrame) -> dict:
    """Every feature held fixed at its typical value — the mean for a numeric column,
    the most frequent value for a categorical one — while the boundary grid varies only
    `feature_x`/`feature_y`. The standard way to read a 2-D slice out of a boundary fit
    on more than two dimensions: everything else stands still.
    """
    representative = {}
    for column in features.columns:
        if pd.api.types.is_numeric_dtype(features[column]):
            representative[column] = features[column].mean()
        else:
            representative[column] = features[column].mode(dropna=True).iloc[0]
    return representative


def _decision_boundary(
    pipeline: Pipeline,
    features: pd.DataFrame,
    target: np.ndarray,
    classes: list[str],
    feature_x: str | None,
    feature_y: str | None,
) -> DecisionBoundary:
    """The grid computation shared by every method with a decision boundary in its
    fixed set (LDA/QDA, #97; KNN, #99). `classes` is supplied rather than read from
    `model.classes_` here, since not every caller's `model` is a plain classifier with
    that attribute (KNN's is a fitted `GridSearchCV`, whose own `.classes_` still works,
    but the point stands for a future method whose doesn't).
    """
    numeric = _numeric_columns(features)
    too_many_classes = len(classes) > MAX_BOUNDARY_CLASSES
    # More than half the rows each getting their own "class" is the signature of a
    # continuous column trained as if it were categorical (price, an ID) — not just a
    # category count too high to plot, a target of the wrong kind entirely.
    looks_continuous = too_many_classes and len(classes) > len(target) / 2

    if len(numeric) < 2 or too_many_classes:
        # Nothing to plot on a grid either way — same reasoning as logistic
        # regression's multiclass ROC: send the facts (`classes`, `numeric_features`),
        # let the caller explain why there's no chart rather than shipping an empty one.
        return DecisionBoundary(
            feature_x=numeric[0] if numeric else "",
            feature_y=numeric[1] if len(numeric) > 1 else "",
            numeric_features=numeric,
            classes=classes,
            grid=[],
            points=[],
            too_many_classes=too_many_classes,
            looks_continuous=looks_continuous,
        )

    if feature_x in numeric and feature_y in numeric and feature_x != feature_y:
        fx, fy = feature_x, feature_y
    else:
        fx, fy = _best_boundary_pair(features, target, numeric)

    representative = _representative_row(features)
    x_min, x_max = features[fx].min(), features[fx].max()
    y_min, y_max = features[fy].min(), features[fy].max()
    # A constant column has no width to draw a grid across — one wide enough to still
    # place the single value in the middle, the same reading `ScatterChart` gives it.
    if x_min == x_max:
        x_min, x_max = x_min - 1, x_max + 1
    if y_min == y_max:
        y_min, y_max = y_min - 1, y_max + 1

    xs = np.linspace(x_min, x_max, BOUNDARY_GRID_RESOLUTION)
    ys = np.linspace(y_min, y_max, BOUNDARY_GRID_RESOLUTION)
    xx, yy = np.meshgrid(xs, ys)

    grid_df = pd.DataFrame([representative] * xx.size).reset_index(drop=True)
    grid_df[fx] = xx.ravel()
    grid_df[fy] = yy.ravel()
    grid_predictions = pipeline.predict(grid_df)

    grid = [
        BoundaryCell(x=float(x), y=float(y), predicted_class=str(p))
        for x, y, p in zip(xx.ravel(), yy.ravel(), grid_predictions, strict=True)
    ]
    points = [
        BoundaryPoint(x=float(x), y=float(y), actual_class=str(t))
        for x, y, t in zip(features[fx], features[fy], target, strict=True)
    ]

    return DecisionBoundary(
        feature_x=fx,
        feature_y=fy,
        numeric_features=numeric,
        classes=classes,
        grid=grid,
        points=points,
        too_many_classes=False,
        looks_continuous=False,
    )


def discriminant_charts(
    pipeline: Pipeline,
    features: pd.DataFrame,
    target: np.ndarray,
    *,
    feature_x: str | None = None,
    feature_y: str | None = None,
) -> DiscriminantCharts:
    model = pipeline.named_steps["model"]
    classes = [str(c) for c in model.classes_]
    predictions = pipeline.predict(features)
    matrix = confusion_matrix(target, predictions, labels=model.classes_)

    return DiscriminantCharts(
        boundary=_decision_boundary(pipeline, features, target, classes, feature_x, feature_y),
        confusion_matrix=ConfusionMatrix(labels=classes, matrix=matrix.tolist()),
    )


def knn_charts(
    pipeline: Pipeline,
    features: pd.DataFrame,
    target: np.ndarray,
    *,
    feature_x: str | None = None,
    feature_y: str | None = None,
) -> KnnCharts:
    """`model` here is the already-fitted `GridSearchCV` `methods.build` wraps K in
    (D-019/D-024's internal tuning) — the tuning curve is read from its own
    `cv_results_`, not a second cross-validation run just to draw a chart.
    """
    model = pipeline.named_steps["model"]
    # A classifier's `classes_` exists on the fitted GridSearchCV (delegated to
    # `best_estimator_`); a regression KNN has none, so `target`'s own distinct values
    # stand in — a continuous target has far more than `MAX_BOUNDARY_CLASSES`, which
    # correctly (if incidentally) reports "too many classes" rather than a boundary
    # fragmented into one region per row.
    classes = (
        [str(c) for c in model.classes_]
        if hasattr(model, "classes_")
        else sorted({str(v) for v in target})
    )
    boundary = _decision_boundary(pipeline, features, target, classes, feature_x, feature_y)

    ks = [int(k) for k in model.cv_results_["param_n_neighbors"]]
    scores = [float(s) for s in model.cv_results_["mean_test_score"]]
    order = sorted(range(len(ks)), key=lambda i: ks[i])
    tuning = TuningCurve(
        points=[TuningPoint(k=ks[i], score=scores[i]) for i in order],
        chosen_k=int(model.best_params_["n_neighbors"]),
    )

    return KnnCharts(boundary=boundary, tuning=tuning)


def _promoted(feature_names: list[str], coefficients: np.ndarray, n: int = 3) -> list[str]:
    order = np.argsort(-np.abs(coefficients))
    return [feature_names[i] for i in order[:n]]


def _regression_shrinkage(
    pipeline: Pipeline, features: pd.DataFrame, target: np.ndarray
) -> tuple[ShrinkagePath, RegularizationCurve]:
    model = pipeline.named_steps["model"]
    prepare = pipeline.named_steps["prepare"]
    feature_names = list(prepare.get_feature_names_out())
    design = np.asarray(prepare.transform(features))

    if isinstance(model, RidgeCV):
        alphas = np.asarray(model.alphas, dtype=float)
        fit_at = Ridge
    else:
        alphas = np.asarray(model.alphas_, dtype=float)
        fit_at = Lasso

    # Neither `*CV`'s own stored curve is usable here: `RidgeCV`'s `cv_results_` is
    # only meaningful in its native per-left-out-sample units — its default `cv=None`
    # runs the efficient LOO algorithm unique to Ridge, and averaging its raw output
    # does not reconstruct `scoring="r2"`, despite that being the metric passed in.
    # `LassoCV`'s own `mse_path_` is a genuine per-fold error, but on the target's raw
    # scale — plotting it next to Ridge's differently-scaled numbers, or against this
    # chart's assumed bounded 0-1 axis, either dwarfs the other or renders as a flat
    # line pinned off-screen. Re-scoring every candidate alpha with a fresh 5-fold R²
    # (`SCORING["regression"]`, methods.py) sidesteps both problems: one comparable,
    # bounded metric for either estimator, on the alpha grid the original tuning
    # already considered.
    scores = np.array(
        [
            cross_val_score(fit_at(alpha=float(a)), design, target, cv=5, scoring="r2").mean()
            for a in alphas
        ]
    )

    order = np.argsort(alphas)
    tuning = RegularizationCurve(
        points=[RegularizationPoint(x=float(alphas[i]), score=float(scores[i])) for i in order],
        chosen_x=float(model.alpha_),
        x_label="α",
    )

    shrinkage_points = [
        ShrinkagePoint(feature=name, x=float(alpha), coefficient=float(coef))
        for alpha in alphas
        for name, coef in zip(
            feature_names,
            np.asarray(fit_at(alpha=float(alpha)).fit(design, target).coef_).ravel(),
            strict=True,
        )
    ]
    promoted = _promoted(feature_names, np.asarray(model.coef_).ravel())

    return ShrinkagePath(points=shrinkage_points, promoted_features=promoted, x_label="α"), tuning


def _classification_shrinkage(
    pipeline: Pipeline, features: pd.DataFrame, target: np.ndarray
) -> tuple[ShrinkagePath, RegularizationCurve]:
    model = pipeline.named_steps["model"]
    prepare = pipeline.named_steps["prepare"]
    feature_names = list(prepare.get_feature_names_out())
    design = np.asarray(prepare.transform(features))

    cs = np.asarray(model.Cs_, dtype=float)
    # `scores_`: (n_folds, n_l1_ratios, n_Cs) with `use_legacy_attributes=False`
    # (methods.py's own setting) — one unified array, not the legacy per-class
    # one-vs-rest dict this had before scikit-learn 1.10. Averaged across folds and
    # the one l1_ratio candidate; `C_` is already a single chosen value under this
    # same setting, not one per class.
    scores = np.mean(model.scores_, axis=(0, 1))
    chosen_x = float(model.C_)

    order = np.argsort(cs)
    tuning = RegularizationCurve(
        points=[RegularizationPoint(x=float(cs[i]), score=float(scores[i])) for i in order],
        chosen_x=chosen_x,
        x_label="C",
    )

    # A multiclass coef_ has one row per class — the same reason Logistic
    # Regression's own coefficient plot is empty past two classes.
    if len(model.classes_) != 2:
        return ShrinkagePath(points=[], promoted_features=[], x_label="C"), tuning

    # `l1_ratio`, not `penalty` — deprecated in scikit-learn 1.8 and removed in 1.10,
    # the same reason `methods.py`'s own `LogisticRegressionCV` construction avoids it.
    l1_ratio = float(model.l1_ratios[0])
    shrinkage_points = [
        ShrinkagePoint(feature=name, x=float(c), coefficient=float(coef))
        for c in cs
        for name, coef in zip(
            feature_names,
            np.asarray(
                LogisticRegression(C=float(c), l1_ratio=l1_ratio, solver="saga", max_iter=2000)
                .fit(design, target)
                .coef_
            ).ravel(),
            strict=True,
        )
    ]
    promoted = _promoted(feature_names, np.asarray(model.coef_).ravel())

    return ShrinkagePath(points=shrinkage_points, promoted_features=promoted, x_label="C"), tuning


def shrinkage_charts(
    pipeline: Pipeline, features: pd.DataFrame, target: np.ndarray, **_unused: object
) -> ShrinkageCharts:
    """`**_unused`: see `linear_regression_charts`."""
    model = pipeline.named_steps["model"]
    if isinstance(model, LogisticRegressionCV):
        shrinkage, tuning = _classification_shrinkage(pipeline, features, target)
    else:
        shrinkage, tuning = _regression_shrinkage(pipeline, features, target)
    return ShrinkageCharts(shrinkage=shrinkage, tuning=tuning)
