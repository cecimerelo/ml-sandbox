"""What Layer 2 learns from: seven properties, banded the way the form reports them.

Seven because Layer 2 trains on sixty rows, which allows roughly that many features before
overfitting becomes the dominant effect — and because the application can only ever supply
these. Anything computed from the raw data would leave the no-dataset path, the one the
tool exists for, unable to use Layer 2 at all (D-028).

Banded rather than exact for the same reason. The benchmark knows `cpu_small` has 8,192
rows, but a user reports `500-10k`, and a model trained on the exact figure would be
served something it never saw. The resolution lost here is resolution the deployed system
never has (D-027).
"""

from __future__ import annotations

from typing import Literal

import numpy as np
import pandas as pd

from mlsandbox.base import StrictModel

Task = Literal["regression", "binary classification", "multiclass classification"]
RowBand = Literal["<500", "500-10k", ">10k"]
FeatureBand = Literal["<10", "10-50", ">50"]
FeatureTypes = Literal["numeric", "categorical", "mixed"]
MissingLevel = Literal["none", "some", "a lot"]
ClassBalance = Literal["roughly equal", "one class dominates", "not applicable"]
DimensionalRegime = Literal["high-dimensional", "moderate", "data-rich"]

SOME_MISSING_THRESHOLD = 0.0
A_LOT_MISSING_THRESHOLD = 0.10
"""FR-1.3 offers none / some / a lot without saying where the lines fall. Any gap at all is
`some`; a tenth of the cells or more is `a lot` — past that, imputation is shaping the data
rather than patching it."""

IMBALANCE_THRESHOLD = 0.20
"""Below this, plain accuracy and balanced accuracy tell the same story; above it they
diverge, which is the distinction the question is actually asking about."""

CATEGORICAL_SHARE_FOR_MIXED = 0.10
"""A dataset is `mixed` once a tenth of its predictors are categorical. One categorical
column among fifty does not change which method suits the data, and calling that mixed
would put almost everything in one band."""

REGIME_BY_BANDS: dict[tuple[str, str], DimensionalRegime] = {
    ("<500", "<10"): "moderate",
    ("<500", "10-50"): "high-dimensional",
    ("<500", ">50"): "high-dimensional",
    ("500-10k", "<10"): "data-rich",
    ("500-10k", "10-50"): "moderate",
    ("500-10k", ">50"): "moderate",
    (">10k", "<10"): "data-rich",
    (">10k", "10-50"): "data-rich",
    (">10k", ">50"): "moderate",
}
"""Observations per predictor, as a stated mapping over the nine band combinations.

Written out rather than computed. Deriving it meant inventing a representative value per
band and dividing, which produces a number to two decimal places from an input that is
"somewhere between 500 and 10,000" — precision the bands do not contain, and thresholds
that then have to be tuned until the arithmetic agrees with judgement. Nine cells can
simply be stated, and each defended.

The reading: few rows with many predictors is where regularisation earns its place and
flexible methods overfit; many rows with few predictors is where flexibility pays.

Given as its own feature rather than left to be inferred from the two bands. They do imply
it, but only through an interaction between categorical variables, and sixty training rows
cannot be relied on to discover an interaction."""


BAND_EXAMPLES: dict[str, int] = {
    "<500": 200,
    "500-10k": 2_000,
    ">10k": 20_000,
    "<10": 6,
    "10-50": 25,
    ">50": 80,
}
"""A value inside each band, for tests and examples only.

Never used to derive a feature — that was the mistake the regime already caught. It exists
so a test can check that a dataset of this size and a form answer of this band produce the
same seven values."""


class MetaFeatures(StrictModel):
    """The seven inputs Layer 2 sees, identical in training and in use."""

    task: Task
    rows: RowBand
    features: FeatureBand
    regime: DimensionalRegime
    feature_types: FeatureTypes
    missing: MissingLevel
    class_balance: ClassBalance

    def as_row(self) -> dict[str, str]:
        """A flat mapping, ready to become one row of the Layer 2 training table."""
        return self.model_dump(mode="json")


def band_task(task: str, n_classes: int | None) -> Task:
    """Regression, binary, or multiclass — as FR-1.3 asks it.

    Three values, not two: the form already distinguishes binary from multiclass, and
    collapsing them would discard information the user has given. It also matters to the
    answer, since several methods handle many classes poorly and imbalance means something
    different across two classes than across twenty-six.
    """
    if task != "classification":
        return "regression"
    return "binary classification" if (n_classes or 0) <= 2 else "multiclass classification"


def band_rows(n_rows: int) -> RowBand:
    if n_rows < 500:
        return "<500"
    return "500-10k" if n_rows <= 10_000 else ">10k"


def band_features(n_features: int) -> FeatureBand:
    if n_features < 10:
        return "<10"
    return "10-50" if n_features <= 50 else ">50"


def band_regime(rows: RowBand, features: FeatureBand) -> DimensionalRegime:
    """Observations per predictor — the axis ISLR reasons along most.

    Derived from the **bands**, never from the raw counts, so both paths reach the same
    answer by construction. Computing it from exact values looked harmless and was not:
    1,000 rows over 20 features gives 50 and reads `moderate`, while the same problem
    described through the form gives 5,000 over 30 and reads `data-rich`. The model would
    have been trained on one and served the other — the exact mismatch D-027 exists to
    prevent, reintroduced by the feature meant to help.
    """
    return REGIME_BY_BANDS[(rows, features)]


def band_missing(rate: float) -> MissingLevel:
    if rate <= SOME_MISSING_THRESHOLD:
        return "none"
    return "some" if rate < A_LOT_MISSING_THRESHOLD else "a lot"


def band_feature_types(n_categorical: int, n_features: int) -> FeatureTypes:
    if n_features == 0 or n_categorical == 0:
        return "numeric"
    if n_categorical == n_features:
        return "categorical"
    share = n_categorical / n_features
    return "mixed" if share >= CATEGORICAL_SHARE_FOR_MIXED else "numeric"


def band_class_balance(task: str, target: np.ndarray | None) -> ClassBalance:
    """How far the classes sit from equal, as the form asks it.

    `not applicable` for regression rather than a guess: the question does not apply, and
    filling it with a default would hand Layer 2 a value that means nothing.
    """
    if task != "classification" or target is None or len(target) == 0:
        return "not applicable"
    _, counts = np.unique(target, return_counts=True)
    proportions = counts / counts.sum()
    deviation = float(np.abs(proportions - 1 / len(proportions)).max())
    return "one class dominates" if deviation >= IMBALANCE_THRESHOLD else "roughly equal"


def from_dataset(
    *,
    task: str,
    features: pd.DataFrame,
    target: np.ndarray | None = None,
    categorical_predictors: int | None = None,
) -> MetaFeatures:
    """Derive the seven from a real dataset, as the upload path does.

    Computed from the frame rather than read from the manifest on purpose: the application
    will have a user's CSV and no manifest, so the same code has to work from the data
    alone or the two paths would diverge.
    """
    n_rows, n_features = features.shape
    n_categorical = (
        categorical_predictors
        if categorical_predictors is not None
        else int(sum(not pd.api.types.is_numeric_dtype(features[c]) for c in features))
    )
    missing_rate = (
        float(features.isna().to_numpy().sum()) / (n_rows * n_features)
        if n_rows and n_features
        else 0.0
    )
    n_classes = len(np.unique(target)) if target is not None and len(target) else None

    return MetaFeatures(
        task=band_task(task, n_classes),
        rows=band_rows(n_rows),
        features=band_features(n_features),
        regime=band_regime(band_rows(n_rows), band_features(n_features)),
        feature_types=band_feature_types(n_categorical, n_features),
        missing=band_missing(missing_rate),
        class_balance=band_class_balance(task, target),
    )


def from_form(
    *,
    task: Task,
    rows: RowBand,
    features: FeatureBand,
    feature_types: FeatureTypes,
    missing: MissingLevel,
    class_balance: ClassBalance,
) -> MetaFeatures:
    """Take the answers straight from the form, as the no-dataset path does.

    The regime is derived from the two bands the user gave rather than asked for: it is a
    consequence of them, and asking a user to estimate observations per predictor would be
    asking them to do arithmetic they came here to avoid.
    """
    return MetaFeatures(
        task=task,
        rows=rows,
        features=features,
        regime=band_regime(rows, features),
        feature_types=feature_types,
        missing=missing,
        class_balance=class_balance,
    )
