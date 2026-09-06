"""The method characteristics table's five axes.

DESIGN.md calls this "the qualitative artifact: theory, no data" — every axis declared,
none measured. Three of the five axes are exactly that; the other two are not, and this
module is a deliberate departure recorded as D-049.

**Accuracy potential and training speed cannot be declared without inventing a claim.**
Nothing in the method registry states an expected accuracy or speed, and asserting one by
hand risks contradicting the benchmark this whole project ran to avoid contradicting: if
the table said "Random Forest: high accuracy" as a theoretical judgement and the benchmark
showed it tying a linear model, the panel would argue with itself in front of the user it
is trying to inform.

So these two axes are computed from the benchmark instead — the same 106-dataset run
Layer 2 trains on, aggregated rather than re-measured. The table and the rest of the tool
end up speaking from one set of numbers.
"""

from __future__ import annotations

from typing import Literal

import pandas as pd

from mlsandbox.base import StrictModel
from mlsandbox.methods import METHODS, Method

Step = Literal[1, 2, 3]
"""Three-step ordinal, low to high. Never the status palette — DESIGN.md is explicit that
this is a rating, not a red/amber/green judgement."""


class Axis(StrictModel):
    word: str
    step: Step


class Characteristics(StrictModel):
    """One method's row in the table."""

    method: str
    label: str
    interpretability: Axis
    handles_non_linearity: Axis
    handles_missing_values: Axis
    accuracy_potential: Axis
    training_speed: Axis


NON_LINEAR_FAMILIES = {"non-linear", "trees", "neural"}
"""Families whose whole point is bending to a shape rather than assuming a straight one.
Everything else in the registry assumes linearity somewhere in its construction — including
the regularised and dimension-reduction families, which shrink or reproject a linear fit
but do not depart from it."""


def _interpretability(method: Method) -> Axis:
    word = {"readable": "high", "with effort": "moderate", "opaque": "low"}[
        method.explainability
    ]
    step: Step = {"high": 3, "moderate": 2, "low": 1}[word]  # type: ignore[assignment]
    return Axis(word=word, step=step)


def _non_linearity(method: Method) -> Axis:
    if method.family in NON_LINEAR_FAMILIES:
        return Axis(word="high", step=3)
    return Axis(word="low", step=1)


def _missing_values(method: Method) -> Axis:
    return Axis(word="yes", step=3) if method.handles_nan else Axis(word="no", step=1)


def _tercile(rank: float, n: int) -> Step:
    """Which third of the field this rank falls in, as a step from 3 (best) to 1 (worst).

    Uses the *proportion* through the field (`(rank - 1) / n`) rather than comparing rank
    directly to `n / 3`. The direct comparison puts a lone entrant — rank 1 of 1 — in the
    bottom third, since `1 <= 1/3` is false: the one method in its task would read as the
    worst rather than as the only one there is.
    """
    proportion = (rank - 1) / n
    if proportion < 1 / 3:
        return 3
    if proportion < 2 / 3:
        return 2
    return 1


def _bucket(rank: float, n: int) -> Axis:
    """Split a rank within its task into thirds, low to high."""
    step = _tercile(rank, n)
    word = {3: "high", 2: "moderate", 1: "lower"}[step]
    return Axis(word=word, step=step)


def _speed_bucket(rank: float, n: int) -> Axis:
    step = _tercile(rank, n)
    word = {3: "fast", 2: "moderate", 1: "slow"}[step]
    return Axis(word=word, step=step)


def from_benchmark(results: pd.DataFrame) -> dict[str, Characteristics]:
    """Build every method's row, with accuracy and speed ranked within their own task.

    Regression's R² and classification's balanced accuracy are not comparable numbers —
    pooling them ranked `linear_regression` below `qda` by an accident of scale rather
    than by how either performs on its own kind of problem. Ranked within task instead.
    """
    ok = results[results.status == "ok"].copy()
    ok["task_kind"] = ok["task"].apply(
        lambda t: "regression" if t == "regression" else "classification"
    )
    by_method_task = ok.groupby(["task_kind", "method"]).agg(
        score=("score", "mean"), speed=("fit_seconds", "mean")
    )

    rows: dict[str, Characteristics] = {}
    for _task_kind, group in by_method_task.groupby(level=0):
        group = group.droplevel(0)
        n = len(group)
        accuracy_rank = group["score"].rank(ascending=False)
        speed_rank = group["speed"].rank(ascending=True)

        for method_name in group.index:
            if method_name in rows:
                continue  # a method scored under both tasks keeps its first table row
            method = METHODS[method_name]
            rows[method_name] = Characteristics(
                method=method_name,
                label=method.label,
                interpretability=_interpretability(method),
                handles_non_linearity=_non_linearity(method),
                handles_missing_values=_missing_values(method),
                accuracy_potential=_bucket(accuracy_rank[method_name], n),
                training_speed=_speed_bucket(speed_rank[method_name], n),
            )
    return rows
