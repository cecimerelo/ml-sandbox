"""Layer 2: what the benchmark taught, made usable.

A regression over (dataset, method) pairs whose target is performance **relative to the
best method on that dataset** — negative regret (D-033). Predicting the winner outright
would have taught it that a method tying with the best is wrong, and predicting raw scores
would have spent half its capacity learning which datasets are easy, which is useless at
recommendation time.

The prediction reads directly as *"how much you lose by choosing this"*, and ordering the
predictions gives the ranked alternatives FR-2.2 needs.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import GroupKFold, cross_val_predict
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

from mlsandbox.base import StrictModel
from mlsandbox.metafeatures import MetaFeatures

META_FEATURE_COLUMNS = [
    "task",
    "rows",
    "features",
    "regime",
    "feature_types",
    "missing",
    "class_balance",
]
"""The seven from D-028. All categorical, all supplied by the form."""

METHOD_COLUMN = "method"

VALIDATION_FOLDS = 5


class Prediction(StrictModel):
    method: str
    expected_shortfall: float
    """Predicted distance below the best available method, in the study's metric. Zero
    means "expected to be the best"; larger means more is given up by choosing it."""

    uncertainty: float
    """Spread of the forest's trees around that prediction.

    Reported because #15's central risk is a meta-model trained on tens of datasets, and a
    confident wrong answer is worse than a hesitant one. Where two methods' intervals
    overlap, the ordering between them is not evidence — and the interface should say so
    rather than present a ranking that looks decisive.
    """

    @property
    def indistinguishable_from(self) -> float:
        """How far another method's prediction can sit and still be within this one's
        spread."""
        return self.expected_shortfall + self.uncertainty


class TrainingTable(StrictModel):
    """The rows Layer 2 learns from, and the dataset each came from.

    `groups` exists so validation can hold out whole datasets. Splitting rows at random
    would put a dataset's other methods in the training set, and the model would recall
    that dataset's scores rather than generalise — inflating every number reported.
    """

    frame: object
    target: object
    groups: object

    model_config = {"arbitrary_types_allowed": True, "frozen": True}


def build_training_table(
    results: pd.DataFrame,
    metafeatures: pd.DataFrame,
    *,
    missing_rate: float = 0.0,
) -> TrainingTable:
    """Join per-dataset method scores to the meta-features describing each dataset.

    Only successful folds contribute, and a method that never ran is absent rather than
    scored zero — the same rule the baselines use, so the two are measured on the same
    ground.
    """
    scored = results[(results.status == "ok") & (results.missing_rate == missing_rate)]
    means = (
        scored.groupby(["dataset", METHOD_COLUMN])["score"].mean().reset_index(name="score")
    )

    # Relative to the best on that dataset. The subtraction is what removes dataset
    # difficulty from the target and leaves only method suitability.
    best = means.groupby("dataset")["score"].transform("max")
    means["shortfall"] = best - means["score"]

    joined = means.merge(metafeatures, on="dataset", how="inner")
    columns = [*META_FEATURE_COLUMNS, METHOD_COLUMN]
    return TrainingTable(
        frame=joined[columns],
        target=joined["shortfall"].to_numpy(),
        groups=joined["dataset"].to_numpy(),
    )


def build_model(seed: int) -> Pipeline:
    """Everything is categorical, so everything is one-hot encoded.

    A forest rather than a linear model: the interactions are the point. "Few rows" means
    something different for a neural network than for a decision tree, and a linear model
    would have to be told each of those crossings explicitly.
    """
    encoder = ColumnTransformer(
        [
            (
                "categories",
                OneHotEncoder(handle_unknown="ignore"),
                [*META_FEATURE_COLUMNS, METHOD_COLUMN],
            )
        ]
    )
    return Pipeline(
        [
            ("encode", encoder),
            # Deliberately small: about 900 rows, and a deeper forest would memorise the
            # datasets rather than the pattern across them.
            (
                "model",
                RandomForestRegressor(
                    n_estimators=300, min_samples_leaf=3, random_state=seed
                ),
            ),
        ]
    )


def cross_validated_predictions(table: TrainingTable, *, seed: int) -> np.ndarray:
    """Predict each row from a model that never saw its dataset.

    Grouped by dataset, not split at random. A random split leaves the same dataset's other
    methods in training, and the model then recalls that dataset's scores instead of
    generalising — which does not fail, it simply reports a better number than is true.
    """
    groups = np.asarray(table.groups)
    n_groups = len(np.unique(groups))
    folds = GroupKFold(n_splits=min(VALIDATION_FOLDS, n_groups))
    return cross_val_predict(
        build_model(seed), table.frame, table.target, groups=groups, cv=folds
    )


def rank_methods(model: Pipeline, features: MetaFeatures, methods: list[str]) -> list[Prediction]:
    """Order the candidate methods for one problem, best first.

    The same call serves both paths: the meta-features arrive identically whether they were
    computed from an uploaded dataset or taken from the form (D-027).
    """
    frame = pd.DataFrame(
        [{**features.as_row(), METHOD_COLUMN: method} for method in sorted(methods)]
    )
    predicted = model.predict(frame)

    # Each tree is one vote; their spread is what the forest does not agree on. A cheap
    # honest uncertainty, rather than a number invented to fill the field.
    encoded = model.named_steps["encode"].transform(frame)
    per_tree = np.stack([tree.predict(encoded) for tree in model.named_steps["model"].estimators_])
    spread = per_tree.std(axis=0)

    return sorted(
        (
            Prediction(
                method=method,
                expected_shortfall=float(value),
                uncertainty=float(deviation),
            )
            for method, value, deviation in zip(
                frame[METHOD_COLUMN], predicted, spread, strict=True
            )
        ),
        key=lambda p: p.expected_shortfall,
    )
