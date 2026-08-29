"""Layer 2.

The test that matters most is the one showing why validation groups by dataset. A random
split does not fail — it simply reports a better number than is true, which is the kind of
error that survives all the way into a thesis.
"""

import numpy as np
import pandas as pd
import pytest
from sklearn.model_selection import cross_val_predict

from mlsandbox.layer2 import (
    build_model,
    build_training_table,
    cross_validated_predictions,
    rank_methods,
)
from mlsandbox.metafeatures import MetaFeatures


def meta_row(dataset: str, rows: str = "500-10k") -> dict:
    return {
        "dataset": dataset,
        "task": "regression",
        "rows": rows,
        "features": "10-50",
        "regime": "moderate",
        "feature_types": "numeric",
        "missing": "none",
        "class_balance": "not applicable",
    }


def result_rows(dataset: str, scores: dict[str, float]) -> list[dict]:
    return [
        {
            "dataset": dataset,
            "method": method,
            "score": score,
            "status": "ok",
            "missing_rate": 0.0,
            "fold": 0,
        }
        for method, score in scores.items()
    ]


@pytest.fixture
def simple_table():
    results = pd.DataFrame(
        result_rows("A", {"forest": 0.90, "linear": 0.60})
        + result_rows("B", {"forest": 0.70, "linear": 0.50})
    )
    metafeatures = pd.DataFrame([meta_row("A"), meta_row("B")])
    return build_training_table(results, metafeatures)


def test_the_target_is_distance_from_the_best_on_that_dataset(simple_table):
    # The subtraction is what removes dataset difficulty and leaves method suitability.
    target = np.asarray(simple_table.target)
    assert sorted(target) == pytest.approx([0.0, 0.0, 0.20, 0.30])


def test_an_easy_and_a_hard_dataset_look_alike_when_the_spread_matches():
    # A: 0.9 vs 0.6. B: 0.5 vs 0.2. Same gap, very different difficulty — and the
    # recommendation should be the same, so the targets should be too.
    results = pd.DataFrame(
        result_rows("easy", {"forest": 0.90, "linear": 0.60})
        + result_rows("hard", {"forest": 0.50, "linear": 0.20})
    )
    table = build_training_table(results, pd.DataFrame([meta_row("easy"), meta_row("hard")]))
    assert sorted(np.asarray(table.target)) == pytest.approx([0.0, 0.0, 0.30, 0.30])


def test_the_best_method_has_a_shortfall_of_zero(simple_table):
    frame = simple_table.frame.copy()
    frame["target"] = simple_table.target
    assert frame[frame.method == "forest"]["target"].tolist() == pytest.approx([0.0, 0.0])


def test_failed_runs_do_not_enter_the_table():
    results = pd.DataFrame(result_rows("A", {"forest": 0.9, "qda": 0.0}))
    results.loc[results.method == "qda", "status"] = "error"
    table = build_training_table(results, pd.DataFrame([meta_row("A")]))
    assert "qda" not in set(table.frame.method)


def test_every_row_records_the_dataset_it_came_from(simple_table):
    # Without this, validation cannot hold out a whole dataset.
    assert sorted(set(simple_table.groups)) == ["A", "B"]


def test_a_random_split_reports_a_better_number_than_is_true():
    """The reason validation groups by dataset.

    Leakage needs a dataset to be identifiable from its features. Here each one has a
    distinct meta-feature combination and a method ordering unrelated to it — so a random
    split lets the model memorise "this combination ranks methods this way" from the
    dataset's other rows, while a grouped split cannot.

    Worth noting that D-033's relative target already removes the easier kind of leakage:
    subtracting the best score per dataset deletes the "this dataset is easy" signal that a
    raw-score model would happily memorise.
    """
    rng = np.random.default_rng(0)
    tasks = ["regression", "binary classification"]
    row_bands = ["<500", "500-10k", ">10k"]
    feature_bands = ["<10", "10-50", ">50"]
    regimes = ["high-dimensional", "moderate", "data-rich"]

    results, metas = [], []
    for index, (task, rows, features, regime) in enumerate(
        [(t, r, f, g) for t in tasks for r in row_bands for f in feature_bands for g in regimes]
    ):
        dataset = f"d{index}"
        metas.append(
            {
                "dataset": dataset,
                "task": task,
                "rows": rows,
                "features": features,
                "regime": regime,
                "feature_types": "numeric",
                "missing": "none",
                "class_balance": "not applicable",
            }
        )
        # An ordering the features cannot predict: only memorising this dataset can.
        ordering = rng.permutation(8)
        results += result_rows(
            dataset, {f"m{j}": 0.9 - 0.05 * int(ordering[j]) for j in range(8)}
        )

    table = build_training_table(pd.DataFrame(results), pd.DataFrame(metas))

    grouped = cross_validated_predictions(table, seed=1)
    random_split = cross_val_predict(build_model(1), table.frame, table.target, cv=5)

    truth = np.asarray(table.target)
    grouped_error = np.abs(grouped - truth).mean()
    random_error = np.abs(random_split - truth).mean()

    assert random_error < grouped_error, (
        f"random {random_error:.4f} should look better than grouped {grouped_error:.4f}"
    )


def test_ranking_puts_the_lowest_shortfall_first(simple_table):
    model = build_model(seed=1).fit(simple_table.frame, simple_table.target)
    features = MetaFeatures(
        task="regression",
        rows="500-10k",
        features="10-50",
        regime="moderate",
        feature_types="numeric",
        missing="none",
        class_balance="not applicable",
    )

    ranked = rank_methods(model, features, ["forest", "linear"])

    assert [p.method for p in ranked] == ["forest", "linear"]
    assert ranked[0].expected_shortfall <= ranked[1].expected_shortfall


def test_ranking_covers_every_candidate_offered(simple_table):
    # FR-2.2 needs the recommendation plus three alternatives, so nothing may be silently
    # dropped from the ordering.
    model = build_model(seed=1).fit(simple_table.frame, simple_table.target)
    features = MetaFeatures(
        task="regression",
        rows="<500",
        features="<10",
        regime="moderate",
        feature_types="numeric",
        missing="none",
        class_balance="not applicable",
    )
    candidates = ["forest", "linear", "unseen_method"]
    assert len(rank_methods(model, features, candidates)) == 3
