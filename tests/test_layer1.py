"""Layer 1: the textbook's claims, written down so the benchmark can test them.

These tests check that the rules say what ISLR says. They are not testing whether the
claims are *true* — that is what the study is for, and a claim that turns out to be wrong
is a result rather than a failing test.
"""

import pytest

from mlsandbox.layer1 import RULES, applicable_rules, recommend
from mlsandbox.metafeatures import MetaFeatures

CLASSIFIERS = [
    "logistic_regression",
    "lda",
    "qda",
    "naive_bayes",
    "knn",
    "ridge",
    "lasso",
    "decision_tree",
    "bagging",
    "random_forest",
    "boosting",
    "svm_linear",
    "svm_rbf",
    "mlp",
]


def problem(**overrides) -> MetaFeatures:
    base = {
        "task": "binary classification",
        "rows": "500-10k",
        "features": "10-50",
        "regime": "moderate",
        "feature_types": "numeric",
        "missing": "none",
        "class_balance": "roughly equal",
    }
    return MetaFeatures(**{**base, **overrides})


def top(features, n=3, **kwargs) -> list[str]:
    return [r.method for r in recommend(features, CLASSIFIERS, **kwargs)[:n]]


def test_few_observations_favour_simple_methods():
    # ISLR's most distinctive claim, and the one the sub-500 band exists to test.
    assert set(top(problem(rows="<500"))) <= {
        "logistic_regression",
        "lda",
        "qda",
        "naive_bayes",
        "decision_tree",
        "ridge",
        "lasso",
    }


def test_critical_interpretability_rules_out_the_black_boxes():
    ranked = top(problem(), n=14, explainability="critical")
    assert ranked.index("logistic_regression") < ranked.index("random_forest")
    assert ranked.index("decision_tree") < ranked.index("mlp")


def test_high_dimensionality_favours_regularisation():
    # Only ridge and lasso among the classifiers: PCR and PLS are regression-only, so the
    # third place would go to whichever untouched method sorts first.
    assert set(top(problem(regime="high-dimensional"), n=2)) == {"ridge", "lasso"}


def test_plenty_of_data_makes_flexibility_affordable():
    ranked = top(problem(regime="data-rich"), n=14)
    assert ranked.index("random_forest") < ranked.index("naive_bayes")


def test_suspected_non_linearity_demotes_the_linear_methods():
    ranked = top(problem(), n=14, suspects_non_linearity=True)
    assert ranked.index("knn") < ranked.index("logistic_regression")


def test_missing_values_favour_trees():
    ranked = top(problem(missing="a lot"), n=14)
    assert ranked.index("random_forest") < ranked.index("svm_rbf")


def test_categorical_features_favour_trees():
    ranked = top(problem(feature_types="mixed"), n=14)
    assert ranked.index("decision_tree") < ranked.index("knn")


def test_a_dominant_class_demotes_the_methods_that_chase_accuracy():
    ranked = top(problem(class_balance="one class dominates"), n=14)
    assert ranked.index("random_forest") < ranked.index("naive_bayes")


def test_no_rule_fires_on_an_unremarkable_problem():
    # A middling problem should not be pushed anywhere. If every rule fired always, the
    # heuristics would carry no information and the study would be measuring nothing.
    assert applicable_rules(problem()) == []


def test_every_recommendation_carries_its_reasons():
    # FR-2.2 needs the decision factors, and they cannot be reconstructed afterwards — the
    # score alone does not say which claims produced it.
    ranked = recommend(problem(rows="<500"), CLASSIFIERS, explainability="critical")
    assert all(r.reasons for r in ranked if r.score != 0)


def test_the_reasons_are_sentences_a_user_could_read():
    # These are the words the explanation layer shows, and the words the thesis quotes when
    # reporting whether each claim survived.
    for rule in RULES:
        assert rule.claim.endswith(".")
        assert len(rule.claim.split()) > 6


def test_ordering_is_deterministic():
    # Left to dictionary order, the same problem could produce different advice between
    # runs, and the study would be measuring the ordering of a hash table.
    features = problem(rows="<500")
    assert top(features, n=14) == top(features, n=14)


def test_only_offered_candidates_are_scored():
    # The rules name methods the caller may not have offered; a recommendation the user
    # cannot act on is worse than none.
    ranked = recommend(problem(), ["knn", "lda"])
    assert {r.method for r in ranked} == {"knn", "lda"}


@pytest.mark.parametrize("rule", RULES, ids=lambda r: r.name)
def test_every_rule_names_methods_and_pushes_somewhere(rule):
    assert rule.methods
    assert rule.weight != 0
