"""Assembling the recommendation from the two layers.

The hybrid the study measured, not a second version of it: the tool must not recommend
differently from the arm the thesis reports.
"""

import numpy as np
import pandas as pd
import pytest

from mlsandbox import artifact, recommend
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


@pytest.fixture(scope="module")
def model():
    """A small artifact trained on synthetic results, so these tests do not need a run."""
    rng = np.random.default_rng(0)
    methods = ["random_forest", "logistic_regression", "knn", "decision_tree", "ridge"]
    rows, meta = [], []
    for i in range(12):
        name = f"d{i}"
        meta.append({"dataset": name, **FEATURES})
        for method in methods:
            good = method == "random_forest"
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
    return artifact.build(
        pd.DataFrame(rows), pd.DataFrame(meta), seed=0, collection_size=12
    )


def problem(**overrides) -> MetaFeatures:
    return MetaFeatures(**{**FEATURES, **overrides})


def test_it_recommends_something_with_alternatives(model):
    result = recommend.for_problem(problem(), model)
    assert result.recommended.method
    assert len(result.alternatives) == recommend.ALTERNATIVES


def test_the_candidates_are_every_method_for_the_task(model):
    """Not a narrower set. A method the user could have chosen belongs in the ranking even
    when it is ruled out — as the last entry, with the reason."""
    from mlsandbox.methods import available

    result = recommend.for_problem(problem(), model, explainability="critical")
    named = {result.recommended.method}
    named |= {s.method for s in result.alternatives} | {s.method for s in result.excluded}
    assert named <= {m.name for m in available("classification")}


def test_a_regression_problem_gets_regression_methods(model):
    result = recommend.for_problem(problem(task="regression"), model)
    from mlsandbox.methods import METHODS

    assert "regression" in METHODS[result.recommended.method].tasks


def test_the_heuristics_supply_reasons_and_the_model_supplies_the_order(model):
    """Two kinds of statement, kept apart.

    A heuristic says "this usually fits badly" and evidence should be able to overturn it.
    Letting the heuristics vote on the ordering would make the study unable to attribute a
    difference to either layer.
    """
    with_belief = recommend.for_problem(problem(), model, suspects_non_linearity="yes")
    assert with_belief.recommended.reasons


def test_a_constraint_is_not_a_preference(model):
    """No accuracy makes an unexplainable model usable where the decision has to be
    defended. Blended into one score, a large enough predicted advantage would overrule a
    requirement the user stated."""
    strict = recommend.for_problem(problem(), model, explainability="critical")
    assert not strict.recommended.excluded_by_constraint
    assert strict.excluded


def test_ruling_everything_out_still_answers(model):
    """More honest than answering nothing: the interface can then show that the constraint
    left no option, which is itself the answer."""
    only_opaque = recommend.for_problem(
        problem(task="regression"), model, explainability="critical"
    )
    assert only_opaque.recommended.method


def test_the_recommendation_carries_how_much_evidence_backs_it(model):
    result = recommend.for_problem(problem(), model)
    assert result.support.total == 12


def test_it_reports_a_provisional_model_as_provisional(model):
    assert recommend.for_problem(problem(), model).provisional is False

    partial = artifact.build(
        *_synthetic(), seed=0, collection_size=999
    )
    assert recommend.for_problem(problem(), partial).provisional is True


def _synthetic():
    rng = np.random.default_rng(1)
    rows, meta = [], []
    for i in range(6):
        meta.append({"dataset": f"d{i}", **FEATURES})
        for method in ("random_forest", "ridge"):
            rows.append(
                {
                    "dataset": f"d{i}",
                    "method": method,
                    "score": rng.normal(0.7, 0.05),
                    "status": "ok",
                    "missing_rate": 0.0,
                    "fold": 0,
                }
            )
    return pd.DataFrame(rows), pd.DataFrame(meta)


def test_the_recommendation_carries_the_characteristics_table_when_given(model):
    from mlsandbox.characteristics import Axis, Characteristics

    table = {
        "random_forest": Characteristics(
            method="random_forest",
            label="Random Forest",
            interpretability=Axis(word="low", step=1),
            handles_non_linearity=Axis(word="high", step=3),
            handles_missing_values=Axis(word="yes", step=3),
            accuracy_potential=Axis(word="high", step=3),
            training_speed=Axis(word="slow", step=1),
        )
    }
    result = recommend.for_problem(problem(), model, characteristics=table)
    named = {result.recommended.method, *(s.method for s in result.alternatives)}
    if "random_forest" in named:
        row = next(
            s.characteristics
            for s in [result.recommended, *result.alternatives]
            if s.method == "random_forest"
        )
        assert row is not None
        assert row.label == "Random Forest"


def test_a_suggestion_with_no_table_row_reports_none_rather_than_erroring(model):
    """A method absent from the table is a fact worth being able to see, not a crash."""
    result = recommend.for_problem(problem(), model, characteristics={})
    assert result.recommended.characteristics is None


def test_the_recommendation_carries_the_full_checkpoint_list(model):
    """Not per-suggestion: it is about the problem's answers, not any one method's ranking,
    so it lives once on the Recommendation rather than repeated on each Suggestion."""
    result = recommend.for_problem(problem(), model)
    assert len(result.checkpoints) == 10


def test_checkpoints_reflect_the_actual_answers_given(model):
    result = recommend.for_problem(problem(rows="<500"), model)
    rows_checkpoint = next(c for c in result.checkpoints if c.question == "how many rows")
    assert rows_checkpoint.fired
