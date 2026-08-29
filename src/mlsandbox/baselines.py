"""What the recommender has to beat.

Two comparators, both computed from the benchmark's results rather than by training
anything: a baseline picks a method name and looks up the score that method already
recorded. That is why the benchmark stores every method on every dataset — without it,
*"what would have happened had I chosen X?"* has no answer.

**Random choice** is the floor. **The single best method** — always recommend whatever
wins most often, ignoring the user's data entirely — is the one that matters, because it
answers the question the thesis has to answer: not *"is this better than guessing?"* but
*"is there any point looking at the user's data at all?"* A recommender that inspects a
problem and cannot beat one that says "use Random Forest" to everybody is not earning its
complexity (D-031).
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from mlsandbox.base import StrictModel

RANDOM_REPETITIONS = 1_000
"""One draw is noise and a repetition costs a table lookup, so the random baseline is
reported as a distribution rather than a single figure — *"0.52 ± 0.04"* rather than
*"0.49"*, which would be an accident of the seed."""

TIE_STD_DEVS = 1.0
"""Two methods are tied when their mean scores fall within this many standard deviations of
each other. The same rule the ranking, the early halt and the interface use — stated once
here so a baseline cannot quietly apply a different one."""


class DatasetScores(StrictModel):
    """Every method's mean score on one dataset, and which of them count as best.

    Ties matter: with fifteen methods and a one-standard-deviation rule, several are
    usually indistinguishable, and calling a single one "the winner" would exaggerate how
    hard the choice is.
    """

    dataset: str
    scores: dict[str, float]
    best_score: float
    winners: list[str]

    def regret(self, method: str) -> float | None:
        """How much is lost by choosing this method instead of the best available.

        None when the method did not run here — a method that errored is absent, not zero
        (D-031). Scoring it as zero would flatter any strategy that avoided it.
        """
        if method not in self.scores:
            return None
        return self.best_score - self.scores[method]

    def is_hit(self, method: str) -> bool:
        """Whether choosing this method counts as finding the best one."""
        return method in self.winners


def summarise(results: pd.DataFrame, *, missing_rate: float = 0.0) -> list[DatasetScores]:
    """Collapse fold-level results into per-dataset method scores.

    Only successful folds contribute. A method whose folds all failed is absent from the
    dataset rather than present with a low score, so nothing distinguishes "did badly" from
    "could not run" by accident.
    """
    frame = results[(results.status == "ok") & (results.missing_rate == missing_rate)]

    summaries: list[DatasetScores] = []
    for dataset, group in frame.groupby("dataset", sort=True):
        stats = group.groupby("method")["score"].agg(["mean", "std", "count"])
        if stats.empty:
            continue

        scores = stats["mean"].to_dict()
        best_method = stats["mean"].idxmax()
        best_score = float(stats.loc[best_method, "mean"])
        # The spread of the best method sets the tie band. Using each method's own spread
        # would make an erratic method easier to tie with, which rewards instability.
        #
        # Guarded against NaN rather than written as `or 0.0`: a single successful fold
        # gives no standard deviation, and NaN is truthy, so that idiom would have carried
        # the NaN into every comparison and emptied the winners list without erroring.
        raw_spread = stats.loc[best_method, "std"]
        spread = 0.0 if pd.isna(raw_spread) else float(raw_spread)

        winners = [
            method
            for method, mean in scores.items()
            if mean >= best_score - TIE_STD_DEVS * spread
        ]
        summaries.append(
            DatasetScores(
                dataset=str(dataset),
                scores={str(k): float(v) for k, v in scores.items()},
                best_score=best_score,
                winners=sorted(winners),
            )
        )
    return summaries


class BaselineResult(StrictModel):
    name: str
    hit_rate: float
    """Share of datasets where the chosen method was among the best."""

    mean_regret: float
    hit_rate_interval: tuple[float, float] | None = None
    """Present only where the baseline is stochastic, from the spread across repetitions."""

    mean_regret_interval: tuple[float, float] | None = None
    detail: str = ""


def random_baseline(
    summaries: list[DatasetScores],
    *,
    seed: int,
    repetitions: int = RANDOM_REPETITIONS,
) -> BaselineResult:
    """Choose uniformly among the methods that ran, once per dataset, many times over.

    Methods that errored are not candidates. Counting a failure as a zero would make random
    look worse and the recommender better by comparison — and a user who picked a method
    and saw an error would try another rather than give up (D-031).
    """
    rng = np.random.default_rng(seed)
    hit_rates, regrets = [], []

    for _ in range(repetitions):
        hits, losses = 0, []
        for summary in summaries:
            candidates = sorted(summary.scores)
            if not candidates:
                continue
            chosen = candidates[rng.integers(len(candidates))]
            hits += summary.is_hit(chosen)
            losses.append(summary.regret(chosen) or 0.0)
        hit_rates.append(hits / len(summaries))
        regrets.append(float(np.mean(losses)))

    return BaselineResult(
        name="random choice",
        hit_rate=float(np.mean(hit_rates)),
        mean_regret=float(np.mean(regrets)),
        hit_rate_interval=_interval(hit_rates),
        mean_regret_interval=_interval(regrets),
        detail=f"uniform over the methods that ran, {repetitions} repetitions",
    )


def single_best_baseline(summaries: list[DatasetScores]) -> BaselineResult:
    """Always recommend the method that wins most often, ignoring the user's data.

    The bar that matters. If a recommender cannot beat this, inspecting the problem is not
    buying anything, and that is the finding — however unwelcome.
    """
    wins: dict[str, int] = {}
    for summary in summaries:
        for method in summary.winners:
            wins[method] = wins.get(method, 0) + 1
    if not wins:
        return BaselineResult(name="single best method", hit_rate=0.0, mean_regret=0.0)

    fixed = max(sorted(wins), key=lambda method: wins[method])
    hits = sum(summary.is_hit(fixed) for summary in summaries)
    # A dataset where the fixed method did not run counts its full best score as regret:
    # a recommendation that cannot be followed is worth nothing to the user.
    losses = [
        summary.regret(fixed) if summary.regret(fixed) is not None else summary.best_score
        for summary in summaries
    ]

    return BaselineResult(
        name="single best method",
        hit_rate=hits / len(summaries),
        mean_regret=float(np.mean(losses)),
        detail=f"always {fixed}, best on {wins[fixed]} of {len(summaries)} datasets",
    )


def _interval(values: list[float]) -> tuple[float, float]:
    """A 95% range across repetitions, as percentiles rather than an assumed distribution."""
    return (float(np.percentile(values, 2.5)), float(np.percentile(values, 97.5)))
