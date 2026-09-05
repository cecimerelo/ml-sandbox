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

EXPLAINABILITY_STRENGTH: dict[Explainability, float] = {
    "not important": 0.0,
    "somewhat": 0.5,
    "critical": 1.0,
}
"""How far the interpretability rules move for each answer.

`somewhat` is half, on the same principle as `SUSPICION_STRENGTH`: a user who says it
matters somewhat has said something, and an answer that changes nothing is a question that
should not have been asked.

This was missed when D-035 made the field three-valued. The field, the form and the
constraint filter all took three levels; `applicable_rules` still asked
`== "critical"`, so in the ranking the user actually sees, `somewhat` behaved exactly like
`not important` — the defect D-035 exists to fix, left live in the one path that shows."""

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


class Factor(StrictModel):
    """One rule that moved a method, and the answer that set it off.

    The trigger is the point. A claim on its own is a statement about method families —
    true, and about nobody's problem in particular. Naming the answer that fired it turns
    it into an account of **this** decision: the explanation becomes traceable to what the
    user said rather than to an authority, which is what FR-2.2 asks for and what FR-2.3
    makes necessary by forbidding a source.
    """

    rule: str
    claim: str

    question: str
    """The form question whose answer fired this, in the words that question uses."""

    answer: str
    """What the user said."""

    favours: bool
    """Whether it pushed this method up or down.

    Both are recorded and only one is shown as a reason. A rule that penalised the
    recommended method is not why it was recommended, and listing it under "what led to
    this" says the opposite of what happened — which is what the panel did before this
    existed.
    """


class Recommendation(StrictModel):
    method: str
    score: float
    factors: list[Factor] = []
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


MISSING_STRENGTH: dict[str, float] = {"none": 0.0, "some": 0.5, "a lot": 1.0}
"""How far the missing-value rule moves.

`some` and `a lot` are not the same situation and must not produce the same advice. Past
about a tenth of the cells, imputation stops patching the data and starts shaping it — the
same threshold the meta-feature bands on — so the method that needs no imputation is worth
more there than where a handful of cells are blank."""

DISTANCE_BASED = ["knn", "svm_rbf"]
"""Methods whose answer depends on how far apart two rows are."""

DIMENSION_REDUCTION = ["pcr", "pls", "lasso", "ridge"]

RULES += [
    Rule(
        name="all-categorical-penalises-distance-methods",
        claim="When every column is a label, 'how far apart are these two rows' stops "
        "having an obvious meaning, and methods built on that question lose their footing.",
        methods=DISTANCE_BASED,
        weight=-1.0,
    ),
    Rule(
        name="many-features-favour-fewer-of-them",
        claim="With a large number of columns, methods that shrink or combine them find "
        "the few that carry the signal instead of giving weight to all of them.",
        methods=DIMENSION_REDUCTION,
        weight=1.0,
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
    """Which claims apply to this problem, at the strength the user's answers give them."""
    rules, _ = _fire(
        features,
        explainability=explainability,
        suspects_non_linearity=suspects_non_linearity,
        suspects_interactions=suspects_interactions,
    )
    return rules


def _fire(
    features: MetaFeatures,
    *,
    explainability: Explainability = "not important",
    suspects_non_linearity: Suspicion = "no",
    suspects_interactions: Suspicion = "no",
) -> tuple[list[Rule], dict[str, tuple[str, str]]]:
    """The rules that apply, and what set each one off.

    Returns both rather than stashing the triggers somewhere for a second call to find.
    Module-level state would be shared across requests, which on a server means one user's
    explanation can be assembled from another user's answers.

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
    # What set each rule off, so the explanation can name the user's own answer back to
    # them rather than restating a claim about method families.
    triggers: dict[str, tuple[str, str]] = {}

    def fire(names: tuple[str, ...] | list[str], question: str, answer: str) -> None:
        fired.extend(names)
        triggers.update(dict.fromkeys(names, (question, answer)))

    if features.rows == "<500":
        fire(
            ["small-sample-favours-simple", "small-sample-penalises-flexible"],
            "how many rows",
            "fewer than 500",
        )
    if features.regime == "high-dimensional":
        fire(
            ["high-dimensional-favours-regularisation"],
            "how many rows and columns",
            f"{features.rows} rows against {features.features} columns",
        )
    if features.regime == "data-rich":
        fire(
            ["data-rich-affords-flexibility"],
            "how many rows and columns",
            f"{features.rows} rows against {features.features} columns",
        )

    interpretability = EXPLAINABILITY_STRENGTH[explainability]
    if interpretability:
        names = ("interpretability-required", "interpretability-rules-out-black-boxes")
        fire(names, "explaining individual predictions", explainability)
        scaled.update(dict.fromkeys(names, interpretability))

    gaps = MISSING_STRENGTH[features.missing]
    if gaps:
        fire(["missing-values-favour-trees"], "how much is missing", features.missing)
        scaled["missing-values-favour-trees"] = gaps

    if features.feature_types in ("categorical", "mixed"):
        fire(
            ["categorical-features-favour-trees"],
            "what kind of columns",
            features.feature_types,
        )
    # `categorical` is not a stronger `mixed`, it is a different problem: with no numeric
    # column left, distance between rows has no natural meaning at all. Without this the
    # two answers produce identical advice, and the question stops being worth asking.
    if features.feature_types == "categorical":
        fire(
            ["all-categorical-penalises-distance-methods"],
            "what kind of columns",
            "all labels",
        )

    # Reaches the rules directly rather than only through the regime. The regime maps nine
    # band pairs onto three values, so two feature bands can land on the same cell — and
    # then answering "more than 50 columns" rather than "10 to 50" changes nothing.
    if features.features == ">50":
        fire(["many-features-favour-fewer-of-them"], "how many columns", "more than 50")

    for answer, question, names in (
        (
            suspects_non_linearity,
            "whether the pattern is a straight line",
            ("non-linearity-penalises-linear-methods", "non-linearity-favours-flexible"),
        ),
        (
            suspects_interactions,
            "whether columns only matter in combination",
            (
                "interactions-favour-methods-that-find-them",
                "interactions-penalise-additive-methods",
            ),
        ),
    ):
        strength = SUSPICION_STRENGTH[answer]
        if strength:
            fire(names, question, answer)
            scaled.update(dict.fromkeys(names, strength))

    if features.class_balance == "one class dominates":
        fire(["imbalance-penalises-naive-methods"], "category sizes", "one dominates")
    if features.task == "multiclass classification":
        fire(
            ["multiclass-penalises-binary-first-methods"],
            "what you are predicting",
            "one of several categories",
        )

    return [
        by_name[name].model_copy(update={"weight": by_name[name].weight * scaled[name]})
        if name in scaled and scaled[name] != 1.0
        else by_name[name]
        for name in fired
    ], triggers


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
    rules, triggers = _fire(
        features,
        explainability=explainability,
        suspects_non_linearity=suspects_non_linearity,
        suspects_interactions=suspects_interactions,
    )

    # The user's constraint is not a preference, so it is applied here rather than left to
    # the caller. Without it the three explainability levels collapse to two in the
    # ranking: scaling both interpretability rules by the same factor preserves the order
    # between readable and opaque methods, so `somewhat` and `critical` are
    # indistinguishable however far they move the weights. What actually separates them is
    # *what each rules out* (D-035), and that has to reach the ordering to be visible.
    blocked = set(excluded_by_constraints(candidates, explainability=explainability))

    scores = dict.fromkeys(candidates, 0.0)
    reasons: dict[str, list[str]] = {method: [] for method in candidates}
    factors: dict[str, list[Factor]] = {method: [] for method in candidates}
    for rule in rules:
        question, answer = triggers.get(rule.name, ("", ""))
        for method in rule.methods:
            if method in scores:
                scores[method] += rule.weight
                reasons[method].append(rule.claim)
                factors[method].append(
                    Factor(
                        rule=rule.name,
                        claim=rule.claim,
                        question=question,
                        answer=answer,
                        favours=rule.weight > 0,
                    )
                )

    # Excluded methods are ranked last, never dropped. Withholding the best option
    # silently leaves the user unable to see what their constraint cost them (D-035).
    return sorted(
        (
            Recommendation(
                method=method,
                score=score,
                reasons=reasons[method],
                factors=factors[method],
            )
            for method, score in scores.items()
        ),
        key=lambda r: (r.method in blocked, -r.score, r.method),
    )
