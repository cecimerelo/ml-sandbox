"""Packaging Layer 2, and the facts that stop a half-trained model shipping quietly.

A model file looks identical whether it was trained on the whole collection or on however
much of it had finished. The difference does not surface as an error — it surfaces as a
recommendation slightly worse than the thesis claims.
"""

import json

import numpy as np
import pandas as pd
import pytest

from mlsandbox import artifact
from mlsandbox.metafeatures import MetaFeatures

FEATURES = dict(
    task="binary classification",
    rows="500-10k",
    features="10-50",
    regime="moderate",
    feature_types="numeric",
    missing="none",
    class_balance="roughly equal",
)
METHODS = ["random_forest", "logistic_regression", "knn", "decision_tree"]


def training_data(n_datasets: int = 12):
    """Results and meta-features for a small synthetic collection."""
    rng = np.random.default_rng(0)
    rows, meta = [], []
    for i in range(n_datasets):
        name = f"d{i}"
        # Wide datasets favour the forest, narrow ones the linear model, so there is a
        # pattern to learn rather than noise to memorise.
        wide = i % 2 == 0
        meta.append({"dataset": name, **FEATURES, "features": ">50" if wide else "<10"})
        for method in METHODS:
            good = method == ("random_forest" if wide else "logistic_regression")
            for fold in range(3):
                rows.append(
                    {
                        "dataset": name,
                        "method": method,
                        "score": (0.9 if good else 0.5) + rng.normal(0, 0.01),
                        "status": "ok",
                        "missing_rate": 0.0,
                        "fold": fold,
                    }
                )
    return pd.DataFrame(rows), pd.DataFrame(meta)


def built(**kwargs):
    results, meta = training_data()
    return artifact.build(results, meta, seed=0, collection_size=12, **kwargs)


def problem(**overrides) -> MetaFeatures:
    return MetaFeatures(**{**FEATURES, **overrides})


# The card


def test_the_card_records_what_the_model_saw():
    card = built().card
    assert card.datasets == 12
    assert card.methods == len(METHODS)
    assert card.observations == 12 * len(METHODS)


def test_the_card_records_the_environment_that_produced_it():
    """So a number can be traced to the code that made it, not to a memory of it."""
    card = built().card
    assert card.python
    assert card.sklearn
    assert card.seed == 0
    assert card.created


def test_a_model_that_saw_the_whole_collection_is_not_provisional():
    assert not built().card.is_provisional


def test_a_model_that_saw_less_than_the_collection_is_provisional():
    """The failure this exists for.

    Building against a partial model is reasonable and packaging one is how you find out
    the pipeline works. Shipping one without noticing is the failure, so the artifact says
    so everywhere it is used.
    """
    results, meta = training_data()
    card = artifact.build(results, meta, seed=0, collection_size=60).card
    assert card.is_provisional
    assert "PROVISIONAL" in card.summary()


def test_results_the_manifest_does_not_know_make_it_provisional():
    """The guard that does not depend on which branch is checked out.

    `collection_size` is read from a file that changes between branches, which is how a
    model trained on sixty datasets first announced itself complete while the collection
    had grown to a hundred and six.
    """
    results, meta = training_data()
    card = artifact.build(
        results, meta, seed=0, collection_size=12, known_datasets={"d0", "d1"}
    ).card
    assert card.unknown_datasets == 10
    assert card.is_provisional


def test_unknown_datasets_are_counted_against_the_results_not_the_training_table():
    """The training table is an inner join with the meta-features, so it silently drops
    every dataset the manifest does not describe. Counting there compares the manifest with
    a set already filtered to match it, and always agrees."""
    results, meta = training_data()
    # A dataset in the results that the meta-features do not describe: it never reaches the
    # training table, and must still be noticed.
    extra = pd.DataFrame(
        [
            {
                "dataset": "unlisted",
                "method": "knn",
                "score": 0.5,
                "status": "ok",
                "missing_rate": 0.0,
                "fold": 0,
            }
        ]
    )
    card = artifact.build(
        pd.concat([results, extra]),
        meta,
        seed=0,
        collection_size=12,
        known_datasets=set(meta.dataset),
    ).card
    assert card.unknown_datasets == 1
    assert card.is_provisional


# Loading


def test_a_saved_artifact_predicts_what_it_predicted(tmp_path):
    """An artifact that does not reproduce its own answers reproduces nothing."""
    original = built()
    path = tmp_path / "layer2.joblib"
    artifact.save(original, path)

    before = [(p.method, p.expected_shortfall) for p in original.rank(problem(), METHODS)]
    after = [(p.method, p.expected_shortfall) for p in artifact.load(path).rank(problem(), METHODS)]
    assert before == after


def test_the_card_survives_the_round_trip(tmp_path):
    path = tmp_path / "layer2.joblib"
    artifact.save(built(), path)
    assert artifact.load(path).card == built().card


def test_a_file_from_another_version_is_refused(tmp_path):
    """A load that accepts a different shape does not fail — it answers, and the answers
    are wrong in a way nothing downstream checks."""
    import joblib

    path = tmp_path / "old.joblib"
    artifact.save(built(), path)
    payload = joblib.load(path)
    payload["card"]["version"] = artifact.ARTIFACT_VERSION + 1
    joblib.dump(payload, path)

    with pytest.raises(ValueError, match="artifact version"):
        artifact.load(path)


def test_the_card_is_readable_without_importing_anything(tmp_path):
    """'What is this file?' is the question asked most often, and a pickle answers it
    worst."""
    path = tmp_path / "layer2.joblib"
    artifact.save(built(), path)
    card = json.loads(path.with_suffix(".json").read_text())
    assert card["datasets"] == 12


# Answering


def test_the_form_only_path_returns_a_ranking():
    """The path the product uses by default. Meta-features arrive identically whether
    computed from a dataset or taken from the form (D-027), so this is the same call —
    which is what makes it work rather than being a second implementation."""
    ranked = built().rank(problem(), METHODS)
    assert [p.method for p in ranked]
    assert sorted(p.method for p in ranked) == sorted(METHODS)


def test_every_prediction_carries_its_uncertainty():
    for prediction in built().rank(problem(), METHODS):
        assert prediction.uncertainty >= 0


def test_the_ranking_reflects_what_was_learned():
    """A model that ranks the same whatever it is asked has learned nothing, and every
    other test here would still pass."""
    wide = built().rank(problem(features=">50"), METHODS)
    narrow = built().rank(problem(features="<10"), METHODS)
    assert [p.method for p in wide] != [p.method for p in narrow]
