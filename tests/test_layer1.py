"""Layer 1: the textbook's claims, written down so the benchmark can test them.

These tests check that the rules say what ISLR says. They are not testing whether the
claims are *true* — that is what the study is for, and a claim that turns out to be wrong
is a result rather than a failing test.
"""

import pytest

from mlsandbox.layer1 import (
    ADDITIVE,
    FINDS_INTERACTIONS,
    RULES,
    SUSPICION_STRENGTH,
    applicable_rules,
    excluded_by_constraints,
    methods_by_explainability,
    recommend,
)
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
    ranked = top(problem(), n=14, suspects_non_linearity="yes")
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


# The user's constraint, and what it rules out


def test_no_constraint_rules_nothing_out():
    assert excluded_by_constraints(CLASSIFIERS, explainability="not important") == []


def test_somewhat_rules_out_only_the_opaque():
    excluded = set(excluded_by_constraints(CLASSIFIERS, explainability="somewhat"))
    assert "random_forest" in excluded
    assert "knn" not in excluded, "KNN can exhibit its neighbours; that is an explanation"


def test_critical_also_rules_out_what_takes_effort():
    somewhat = set(excluded_by_constraints(CLASSIFIERS, explainability="somewhat"))
    critical = set(excluded_by_constraints(CLASSIFIERS, explainability="critical"))
    assert somewhat < critical


def test_the_middle_answer_does_something():
    """The form offers three levels, so all three have to differ.

    An option that behaves identically to another asks the user a question that changes
    nothing, which is worse than not asking it.
    """
    outcomes = {
        level: tuple(excluded_by_constraints(CLASSIFIERS, explainability=level))
        for level in ("not important", "somewhat", "critical")
    }
    assert len(set(outcomes.values())) == 3


def test_readable_methods_survive_every_constraint():
    assert not excluded_by_constraints(
        methods_by_explainability("readable"), explainability="critical"
    )


def test_the_excluded_are_returned_not_hidden():
    """The cost of the constraint has to be visible, or the user cannot weigh it."""
    assert excluded_by_constraints(CLASSIFIERS, explainability="critical")


def test_layer_one_does_not_keep_its_own_copy_of_who_is_explainable():
    """One source of truth: the method registry.

    A second copy here would drift, and the failure is silent — the ranking penalises a
    method for being opaque while the filter lets it through, producing a coherent and
    wrong recommendation.
    """
    from mlsandbox.methods import METHODS

    rule = next(r for r in RULES if r.name == "interpretability-rules-out-black-boxes")
    assert set(rule.methods) == {
        m.name for m in METHODS.values() if m.explainability == "opaque"
    }


def test_a_rule_scores_each_method_once():
    """The groups overlap, so a rule can name the same method twice.

    Ridge is both regularised and readable. Scored per occurrence, it would collect the
    weight twice and show the same claim twice in its explanation.
    """
    for rule in RULES:
        assert len(rule.methods) == len(set(rule.methods)), rule.name


# What the user believes about the shape of their data


@pytest.mark.parametrize("question", ["suspects_interactions", "suspects_non_linearity"])
def test_all_three_answers_behave_differently(question):
    """The form offers three options, so three things have to happen.

    An option that behaves identically to another asks the user a question that changes
    nothing — the fault D-035 fixed for explainability, and the reason this task exists.
    """
    outcomes = {
        answer: tuple(
            (r.method, r.score)
            for r in recommend(problem(), CLASSIFIERS, **{question: answer})
        )
        for answer in ("no", "unsure", "yes")
    }
    assert len(set(outcomes.values())) == 3


@pytest.mark.parametrize("question", ["suspects_interactions", "suspects_non_linearity"])
def test_no_fires_nothing(question):
    assert applicable_rules(problem(), **{question: "no"}) == []


@pytest.mark.parametrize("question", ["suspects_interactions", "suspects_non_linearity"])
def test_unsure_moves_half_as_far_as_yes(question):
    """A hedge that moves as much as a conviction is not a hedge."""
    unsure = applicable_rules(problem(), **{question: "unsure"})
    certain = applicable_rules(problem(), **{question: "yes"})
    assert [r.name for r in unsure] == [r.name for r in certain]
    for hedged, sure in zip(unsure, certain, strict=True):
        assert hedged.weight == pytest.approx(sure.weight * SUSPICION_STRENGTH["unsure"])


@pytest.mark.parametrize("question", ["suspects_interactions", "suspects_non_linearity"])
def test_hedging_does_not_change_what_the_user_is_told(question):
    """Only how far the claim moves the ranking changes with confidence — not the claim.

    Rewording an explanation because the user was unsure would make the tool's reasoning
    depend on the user's confidence, which is not something the textbook has an opinion
    about.
    """
    unsure = applicable_rules(problem(), **{question: "unsure"})
    certain = applicable_rules(problem(), **{question: "yes"})
    assert [r.claim for r in unsure] == [r.claim for r in certain]


def test_suspected_interactions_favour_methods_that_find_them():
    ranked = top(problem(), n=4, suspects_interactions="yes")
    assert set(ranked) <= set(FINDS_INTERACTIONS)


def test_suspected_interactions_demote_the_additive_methods():
    ranked = [
        r.method for r in recommend(problem(), CLASSIFIERS, suspects_interactions="yes")
    ]
    for method in ("naive_bayes", "logistic_regression", "lda"):
        assert ranked.index(method) > ranked.index("random_forest")


def test_naive_bayes_counts_as_additive():
    """Its independence assumption is the interaction assumption, negated.

    Conditional independence says the predictors carry no joint information — which is
    exactly what a suspected interaction denies.
    """
    assert "naive_bayes" in ADDITIVE


def test_a_gam_is_additive_by_construction():
    """The sum of per-feature curves is the whole of its form, not an incidental limit."""
    assert "gam" in ADDITIVE


def test_no_method_both_finds_and_misses_interactions():
    assert not set(ADDITIVE) & set(FINDS_INTERACTIONS)


def test_the_two_beliefs_are_asked_and_answered_separately():
    """Non-linearity and interactions are different claims about the data.

    A curved relationship in one variable is not a joint effect between two, and a method
    can handle one without the other — splines bend, and are still additive.
    """
    curved = recommend(problem(), CLASSIFIERS, suspects_non_linearity="yes")
    joint = recommend(problem(), CLASSIFIERS, suspects_interactions="yes")
    assert [(r.method, r.score) for r in curved] != [(r.method, r.score) for r in joint]
