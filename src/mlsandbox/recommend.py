"""The recommendation, assembled from the two layers.

Neither layer is re-implemented here. Layer 1 holds the textbook's claims and the user's
constraints; Layer 2 holds what the benchmark taught. This module decides how they meet,
which is the hybrid strategy the study measured (D-035) — the same code path, so the tool
cannot recommend differently from the arm the thesis reports.

Two kinds of statement, kept apart. A heuristic says *"this usually fits badly"* and
evidence should be able to overturn it. A constraint says *"I cannot use this"*, and no
accuracy makes an unexplainable model usable where the decision has to be defended. Folded
into one score, a large enough predicted advantage would overrule a requirement the user
stated.
"""

from __future__ import annotations

from mlsandbox import layer1
from mlsandbox.artifact import Artifact, Support
from mlsandbox.base import StrictModel
from mlsandbox.metafeatures import MetaFeatures
from mlsandbox.methods import METHODS, Method, available

FLEXIBILITY_LABEL: dict[str, str] = {
    "linear": "assumes a straight-line relationship",
    "regularisation": "assumes a straight-line relationship, held back deliberately",
    "discriminant": "assumes a simple boundary between classes",
    "dimension-reduction": "assumes a straight-line relationship, in fewer dimensions",
    "non-linear": "bends to follow curves in the data",
    "trees": "splits the data repeatedly rather than fitting a single shape",
    "svm": "assumes a fixed boundary shape",
    "neural": "bends to follow arbitrary shapes in the data",
}
"""Where a method's family sits on the bias-variance axis, in words rather than a number.

Read off the family (D-019's grouping) because that is what actually determines it — a
linear model is inflexible whether or not it is the one recommended, and restating that
per suggestion would be the same sentence with the method's name swapped in."""

INTERPRETABILITY_DETAIL: dict[str, str] = {
    "readable": "you can read the reason for any single answer directly from the model.",
    "with effort": "the reason for an answer can be recovered, but takes work to extract.",
    "opaque": "there is no single reason to give for one answer — only patterns across many.",
}


def _position(method: Method) -> tuple[Position, Position]:
    flexibility = Position(
        label="flexible" if method.family in ("non-linear", "trees", "neural") else "simple",
        detail=FLEXIBILITY_LABEL.get(method.family, "follows a fixed shape"),
    )
    interpretability = Position(
        label=method.explainability,
        detail=INTERPRETABILITY_DETAIL[method.explainability],
    )
    return flexibility, interpretability


class DecisionFactor(StrictModel):
    """One of the user's answers, and what it argued for.

    A claim on its own is a statement about method families: true, and about nobody's
    problem in particular. Named against the answer that fired it and the method it
    displaced, it becomes an account of **this** decision — traceable to what the user
    said rather than to an authority, which is what FR-2.2 asks for and what FR-2.3 makes
    necessary by forbidding a source.
    """

    question: str
    answer: str
    claim: str

    over: str | None = None
    """The best-ranked method this same rule pushed down, if any.

    The contrast is what makes the factor concrete. "Fewer than 500 rows favours a
    decision tree" is a fact; "fewer than 500 rows, so a decision tree rather than a random
    forest" is an answer to *why not the other one* — which is the question a reader
    actually has.
    """


class Position(StrictModel):
    """Where this method sits on one of ISLR's two axes, in the words a user reads.

    Not a definition of the axis — that duplicates what the panel's fixed prose already
    says. This is the one fact specific to *this* method: where it falls, and the
    consequence of that for the person reading it.
    """

    label: str
    """Where the method sits, e.g. "flexible" or "readable"."""

    detail: str
    """What that means for this method, in one sentence."""


class Suggestion(StrictModel):
    """One method, where it is expected to land, and why it was put there."""

    method: str
    label: str

    flexibility: Position
    interpretability: Position

    expected_shortfall: float
    """Predicted distance below the best available method. Zero means "expected to be the
    best"; larger means more is given up by choosing it."""

    uncertainty: float
    """Spread across the forest's trees.

    Carried through because #15's central risk is a meta-model trained on around a hundred
    datasets. Where two methods' intervals overlap the ordering between them is not
    evidence, and the interface has to be able to say so rather than present a ranking that
    looks decisive.
    """

    reasons: list[str]
    """The claims that fired, in the words shown to the user.

    Produced here rather than reconstructed later, because a score cannot be turned back
    into the reasoning that made it (FR-2.2).
    """

    factors: list[DecisionFactor] = []
    """Why this method, in terms of what the user said.

    Only the ones that pushed it **up**. A rule that penalised the recommended method is
    not why it was recommended, and listing it under "what led to this" says the opposite
    of what happened — which is what the panel did until someone read it.
    """

    excluded_by_constraint: bool = False
    """Ruled out by something the user said they need, not by the evidence.

    Returned rather than dropped: withholding the best method silently leaves the user
    unable to see what their constraint cost them (D-035).
    """


class Recommendation(StrictModel):
    """What the engine answers with."""

    recommended: Suggestion
    alternatives: list[Suggestion]
    excluded: list[Suggestion]

    support: Support
    """How much evidence the study has for a problem shaped like this one.

    Reported because the model's own uncertainty does not carry it and was measured not to
    (#17): tree spread tracks how hard a region is, not how unfamiliar.
    """

    provisional: bool
    """Whether the model behind this was trained on a finished benchmark."""


ALTERNATIVES = 3
"""How many alternatives accompany the recommendation (FR-2.2)."""


def for_problem(
    features: MetaFeatures,
    artifact: Artifact,
    *,
    explainability: layer1.Explainability = "not important",
    suspects_non_linearity: layer1.Suspicion = "no",
    suspects_interactions: layer1.Suspicion = "no",
) -> Recommendation:
    """Rank the methods that apply to this problem, best first.

    The candidate set is every method that applies to the task, and nothing narrower. A
    method the user could have chosen belongs in the ranking even when it is ruled out — as
    the last entry, with the reason, so the cost of a constraint is visible.
    """
    task = "regression" if features.task == "regression" else "classification"
    candidates = sorted(method.name for method in available(task))

    # Layer 1 supplies the reasons and the constraint; Layer 2 supplies the ordering.
    # The heuristics deliberately do not vote on the order: a model trained on real
    # results is better placed to judge, and mixing the two would make the study unable to
    # attribute a difference to either.
    scored = layer1.recommend(
        features,
        candidates,
        explainability=explainability,
        suspects_non_linearity=suspects_non_linearity,
        suspects_interactions=suspects_interactions,
    )
    reasoned = {r.method: r.reasons for r in scored}
    penalised_by = _penalised_by(scored)
    blocked = set(
        layer1.excluded_by_constraints(candidates, explainability=explainability)
    )

    ranked = artifact.rank(features, candidates)
    position = {p.method: i for i, p in enumerate(ranked)}
    by_method = {r.method: r for r in scored}

    ordered = []
    for p in ranked:
        flexibility, interpretability = _position(METHODS[p.method])
        ordered.append(
            Suggestion(
                method=p.method,
                label=METHODS[p.method].label,
                flexibility=flexibility,
                interpretability=interpretability,
                expected_shortfall=p.expected_shortfall,
                uncertainty=p.uncertainty,
                reasons=reasoned.get(p.method, []),
                factors=_factors_for(by_method.get(p.method), penalised_by, position),
                excluded_by_constraint=p.method in blocked,
            )
        )

    allowed = [s for s in ordered if not s.excluded_by_constraint]
    excluded = [s for s in ordered if s.excluded_by_constraint]

    # Every method ruled out. Recommending one anyway is more honest than answering
    # nothing: the interface can then show that the constraint left no option, which is
    # itself the answer.
    usable = allowed or excluded

    return Recommendation(
        recommended=usable[0],
        alternatives=usable[1 : 1 + ALTERNATIVES],
        excluded=excluded if allowed else [],
        support=artifact.support(features),
        provisional=artifact.card.is_provisional,
    )


def _penalised_by(
    scored: list[layer1.Recommendation],
) -> dict[tuple[str, str], list[str]]:
    """Which methods each **answer** pushed down.

    Keyed on the answer rather than the rule, because the rules come in pairs: *"few
    observations favour simple methods"* and *"few observations penalise flexible ones"*
    are two rules fired by one answer. Grouping by rule finds nothing to contrast with,
    since a favouring rule penalises nobody by construction.

    The user does not have rules, they have answers. The contrast they want is what their
    answer argued against.
    """
    penalised: dict[tuple[str, str], list[str]] = {}
    for recommendation in scored:
        for factor in recommendation.factors:
            if not factor.favours:
                penalised.setdefault((factor.question, factor.answer), []).append(
                    recommendation.method
                )
    return penalised


def _factors_for(
    scored: layer1.Recommendation | None,
    penalised_by: dict[tuple[str, str], list[str]],
    position: dict[str, int],
) -> list[DecisionFactor]:
    """The answers that argued *for* this method, each against what it displaced.

    The contrast is the best-ranked method the **same answer** pushed down — the one the
    reader would otherwise ask about. Where an answer pushed nothing down, the factor
    stands alone rather than inventing an opponent.
    """
    if scored is None:
        return []

    factors = []
    for factor in scored.factors:
        if not factor.favours:
            continue
        displaced = sorted(
            penalised_by.get((factor.question, factor.answer), []),
            key=lambda m: position.get(m, len(position)),
        )
        factors.append(
            DecisionFactor(
                question=factor.question,
                answer=factor.answer,
                claim=factor.claim,
                over=METHODS[displaced[0]].label if displaced else None,
            )
        )
    return factors
