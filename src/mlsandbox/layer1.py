"""Layer 1: the textbook's advice, written down so it can be tested.

This is the object of study, not a feature of the application. The thesis asks whether the
heuristics taught in a statistical learning course predict real performance — and a
question like that needs the guidance stated explicitly before the benchmark can be asked
whether it holds.

Every rule below is a claim ISLR makes. Each carries the reasoning a user is shown, which
is the same sentence the thesis will quote when reporting whether the claim survived
contact with the data.

A rule that turns out to be wrong is a result, not an embarrassment. The reporting is
built so that conclusion is presentable.
"""

from __future__ import annotations

from typing import Literal

from pydantic import field_validator

from mlsandbox.base import StrictModel
from mlsandbox.metafeatures import MetaFeatures
from mlsandbox.methods import METHODS

Explainability = Literal["not important", "somewhat", "critical"]
"""How much the user needs to justify individual predictions — a constraint they state,
never a property of the data, which is why it reaches Layer 1 and never Layer 2 (D-026).

Three values because the form offers three, and they map onto the three levels a method
can have. Anything coarser would make `somewhat` behave identically to `not important`,
which is worse than not asking: the user answers a question that changes nothing."""

Suspicion = Literal["no", "unsure", "yes"]
"""What the user believes about their data's shape — a belief, not a measurement, which is
why it reaches Layer 1 and never Layer 2 (D-026).

Three values because FR-1.4 asks for three. Held as a boolean, `unsure` behaves exactly
like `no` and the user answers a question that changes nothing — the same fault D-035 fixed
for explainability."""

SUSPICION_STRENGTH: dict[Suspicion, float] = {"no": 0.0, "unsure": 0.5, "yes": 1.0}
"""How far an answer moves the rules that depend on it.

`unsure` tilts rather than abstains, and it tilts toward flexibility, because **the cost of
being wrong is asymmetric**. Assume additivity when the truth is not additive and a linear
model cannot recover: the surface it needs is not in the space of functions it can fit.
Assume flexibility when the truth is additive and a flexible method can still represent a
line — it pays variance for the privilege, but it gets there.

Half rather than full, because a hedge that moves as much as a conviction is not a hedge,
and `unsure` would then be indistinguishable from `yes`."""

EXCLUDED_BY: dict[Explainability, tuple[str, ...]] = {
    "not important": (),
    "somewhat": ("opaque",),
    "critical": ("opaque", "with effort"),
}
"""Which method explainability levels each answer rules out.

`somewhat` drops what cannot be explained at all; `critical` also drops what can only be
explained with work, because "I must justify this decision" is not met by a method whose
reasoning has to be reconstructed each time."""


def methods_by_explainability(level: str) -> list[str]:
    """Read from the method registry rather than restated here.

    Whether a method is explainable is a property of the method, and the registry is where
    those live. Keeping a second copy in this module would mean two places to update when a
    method is added — and when they drift, the ranking penalises a method for being opaque
    while the filter lets it through. That does not fail; it produces a coherent, wrong
    answer."""
    return sorted(m.name for m in METHODS.values() if m.explainability == level)


def excluded_by_constraints(
    candidates: list[str], *, explainability: Explainability
) -> list[str]:
    """Methods the user's stated constraint rules out, whatever the data says.

    Kept apart from the scoring below because it is a different kind of claim. A rule with
    a large negative weight says *"this usually fits badly"*, and enough evidence should be
    able to overturn it. A constraint says *"I cannot use this"*, and no accuracy makes an
    unexplainable model usable where the decision has to be defended. Folded into one
    score, a strong enough result would quietly overrule a requirement the user stated.

    What is excluded is returned, not silently dropped. Withholding the best method leaves
    the user unable to see what the constraint cost them, so the caller reports the gap and
    the choice stays with the person who set it (D-035).
    """
    blocked = {
        level_method
        for level in EXCLUDED_BY[explainability]
        for level_method in methods_by_explainability(level)
    }
    return [method for method in candidates if method in blocked]


class Rule(StrictModel):
    """One claim from the textbook, and the score it moves."""

    name: str
    claim: str
    """What ISLR asserts, in the words the explanation layer shows a user."""

    methods: list[str]
    weight: float
    """How strongly the rule pushes. Positive favours, negative discourages."""

    @field_validator("methods")
    @classmethod
    def _each_method_once(cls, methods: list[str]) -> list[str]:
        """A rule applies to a method once, however the list was assembled.

        The groups overlap — ridge is both regularised and readable — so a rule written as
        `INTERPRETABLE + REGULARISED` names it twice. Scoring walks the list, so it would
        collect the weight twice and show its claim twice in the explanation: a method
        favoured for one reason ranked as though it had two.
        """
        return list(dict.fromkeys(methods))


class Recommendation(StrictModel):
    method: str
    score: float
    reasons: list[str]
    """The claims that fired, in the order they were applied. This is the explanation —
    FR-2.2 needs the decision factors, and they cannot be reconstructed after the fact."""


FLEXIBLE = ["random_forest", "boosting", "bagging", "mlp", "svm_rbf", "knn"]
INTERPRETABLE = methods_by_explainability("readable")
REGULARISED = ["ridge", "lasso", "pcr", "pls"]
TREES = ["decision_tree", "random_forest", "boosting", "bagging"]
NON_LINEAR = ["splines", "polynomial", "knn", "svm_rbf", *TREES, "mlp"]

FINDS_INTERACTIONS = [*TREES, "mlp", "svm_rbf", "knn"]
"""Methods that pick up a joint effect without being told to look for one. A tree's second
split is conditional on its first, which is what an interaction is; kernels and hidden
layers get there by a different route."""

ADDITIVE = ["linear_regression", "logistic_regression", "lda", "gam", "naive_bayes"]
"""Methods that model each predictor's contribution separately and sum them.

Additive by construction, not by accident: a GAM's whole form is a sum of per-feature
curves, and naive Bayes assumes the predictors are conditionally independent — which is
the assumption an interaction violates by definition. They can represent one only if a
person works out which one and writes the product term in by hand."""

RULES: list[Rule] = [
    Rule(
        name="small-sample-favours-simple",
        claim="With few observations, flexible methods have too little data to learn from "
        "and fit noise instead of pattern.",
        methods=INTERPRETABLE + REGULARISED,
        weight=1.0,
    ),
    Rule(
        name="small-sample-penalises-flexible",
        claim="With few observations, a flexible method can describe the data it was "
        "given almost perfectly and still fail on anything new.",
        methods=FLEXIBLE,
        weight=-1.0,
    ),
    Rule(
        name="high-dimensional-favours-regularisation",
        claim="When predictors approach the number of observations, shrinking or "
        "discarding coefficients is what keeps a model from chasing noise.",
        methods=REGULARISED,
        weight=1.5,
    ),
    Rule(
        name="data-rich-affords-flexibility",
        claim="With plenty of observations per predictor, a flexible method has enough "
        "data to justify its variance.",
        methods=FLEXIBLE,
        weight=1.0,
    ),
    Rule(
        name="interpretability-required",
        claim="A model whose reasoning cannot be read is unusable where the decision must "
        "be justified.",
        methods=INTERPRETABLE,
        weight=2.0,
    ),
    Rule(
        name="interpretability-rules-out-black-boxes",
        claim="Ensembles and neural networks give predictions, not explanations.",
        methods=methods_by_explainability("opaque"),
        weight=-2.0,
    ),
    Rule(
        name="missing-values-favour-trees",
        claim="Tree-based methods handle gaps natively; other methods need the gaps filled "
        "in first, which distorts the relationships they estimate.",
        methods=TREES,
        weight=1.0,
    ),
    Rule(
        name="categorical-features-favour-trees",
        claim="Trees split on categories directly, where other methods need them encoded "
        "into columns that may outnumber the observations.",
        methods=TREES,
        weight=0.5,
    ),
    Rule(
        name="non-linearity-penalises-linear-methods",
        claim="A straight line cannot follow a curved relationship, however much data it "
        "is given.",
        methods=["linear_regression", "logistic_regression", "lda"],
        weight=-1.0,
    ),
    Rule(
        name="non-linearity-favours-flexible",
        claim="Methods that bend to the data can follow a relationship a line cannot.",
        methods=NON_LINEAR,
        weight=1.0,
    ),
    Rule(
        name="imbalance-penalises-naive-methods",
        claim="When one class dominates, methods that optimise raw accuracy learn to "
        "predict that class and little else.",
        methods=["naive_bayes", "knn"],
        weight=-0.5,
    ),
    Rule(
        name="multiclass-penalises-binary-first-methods",
        claim="Some methods extend to many classes only by fitting a separate model per "
        "class, which multiplies both cost and variance.",
        methods=["svm_linear", "svm_rbf", "logistic_regression"],
        weight=-0.5,
    ),
]


INTERACTION_RULES = [
    Rule(
        name="interactions-favour-methods-that-find-them",
        claim="When two variables only matter together, methods that split the data "
        "repeatedly find that combination on their own.",
        methods=FINDS_INTERACTIONS,
        weight=1.0,
    ),
    Rule(
        name="interactions-penalise-additive-methods",
        claim="Some methods add up each variable's effect separately, so a combined effect "
        "is invisible to them unless someone works out which combination matters and "
        "writes it in by hand.",
        methods=ADDITIVE,
        weight=-1.0,
    ),
]
"""Kept beside the rest by `RULES` below. Named separately only so the two claims that
answer FR-1.4's interaction question can be found together."""

RULES += INTERACTION_RULES


def applicable_rules(
    features: MetaFeatures,
    *,
    explainability: Explainability = "not important",
    suspects_non_linearity: Suspicion = "no",
    suspects_interactions: Suspicion = "no",
) -> list[Rule]:
    """Which claims apply to this problem, at the strength the user's answers give them.

    The three user inputs come from the person rather than the data (FR-1.4). They are
    constraints and beliefs, not measurable properties, which is exactly why they belong
    here and not in the trained model (D-026).

    Rules whose strength is not full are returned as scaled copies — same name, same claim,
    smaller weight. The explanation a user reads does not change with their confidence;
    only how far it moves the ranking does.
    """
    by_name = {rule.name: rule for rule in RULES}
    fired: list[str] = []
    scaled: dict[str, float] = {}

    if features.rows == "<500":
        fired += ["small-sample-favours-simple", "small-sample-penalises-flexible"]
    if features.regime == "high-dimensional":
        fired.append("high-dimensional-favours-regularisation")
    if features.regime == "data-rich":
        fired.append("data-rich-affords-flexibility")

    if explainability == "critical":
        fired += ["interpretability-required", "interpretability-rules-out-black-boxes"]

    if features.missing in ("some", "a lot"):
        fired.append("missing-values-favour-trees")
    if features.feature_types in ("categorical", "mixed"):
        fired.append("categorical-features-favour-trees")

    for answer, names in (
        (
            suspects_non_linearity,
            ("non-linearity-penalises-linear-methods", "non-linearity-favours-flexible"),
        ),
        (
            suspects_interactions,
            (
                "interactions-favour-methods-that-find-them",
                "interactions-penalise-additive-methods",
            ),
        ),
    ):
        strength = SUSPICION_STRENGTH[answer]
        if strength:
            fired += names
            scaled.update(dict.fromkeys(names, strength))

    if features.class_balance == "one class dominates":
        fired.append("imbalance-penalises-naive-methods")
    if features.task == "multiclass classification":
        fired.append("multiclass-penalises-binary-first-methods")

    return [
        by_name[name].model_copy(update={"weight": by_name[name].weight * scaled[name]})
        if name in scaled and scaled[name] != 1.0
        else by_name[name]
        for name in fired
    ]


def recommend(
    features: MetaFeatures,
    candidates: list[str],
    *,
    explainability: Explainability = "not important",
    suspects_non_linearity: Suspicion = "no",
    suspects_interactions: Suspicion = "no",
) -> list[Recommendation]:
    """Score every candidate method by the claims that apply, best first.

    Ties are broken by name so the output is deterministic. Left to dictionary order, the
    same problem could produce different advice between runs, and the study would be
    measuring the ordering of a hash table.
    """
    rules = applicable_rules(
        features,
        explainability=explainability,
        suspects_non_linearity=suspects_non_linearity,
        suspects_interactions=suspects_interactions,
    )

    scores = dict.fromkeys(candidates, 0.0)
    reasons: dict[str, list[str]] = {method: [] for method in candidates}
    for rule in rules:
        for method in rule.methods:
            if method in scores:
                scores[method] += rule.weight
                reasons[method].append(rule.claim)

    return sorted(
        (
            Recommendation(method=method, score=score, reasons=reasons[method])
            for method, score in scores.items()
        ),
        key=lambda r: (-r.score, r.method),
    )
