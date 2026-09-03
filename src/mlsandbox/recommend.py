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
from mlsandbox.methods import METHODS, available


class Suggestion(StrictModel):
    """One method, where it is expected to land, and why it was put there."""

    method: str
    label: str

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
    reasoned = {
        r.method: r.reasons
        for r in layer1.recommend(
            features,
            candidates,
            explainability=explainability,
            suspects_non_linearity=suspects_non_linearity,
            suspects_interactions=suspects_interactions,
        )
    }
    blocked = set(
        layer1.excluded_by_constraints(candidates, explainability=explainability)
    )

    ordered = [
        Suggestion(
            method=p.method,
            label=METHODS[p.method].label,
            expected_shortfall=p.expected_shortfall,
            uncertainty=p.uncertainty,
            reasons=reasoned.get(p.method, []),
            excluded_by_constraint=p.method in blocked,
        )
        for p in artifact.rank(features, candidates)
    ]

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
