"""The evaluation harness: every method, on every dataset, on identical folds.

Sequential by design. Running one thing at a time makes the timeout a signal rather than a
process to kill and reap, keeps the machine usable, and makes a failure attributable to
the line above it. A full run is hours, so it writes incrementally and resumes, and the
`--sample` mode exists so debugging costs a minute rather than an evening.
"""

from __future__ import annotations

import signal
import time
from collections.abc import Callable, Iterator
from dataclasses import dataclass, field

import numpy as np
import pandas as pd
from sklearn.base import clone
from sklearn.metrics import balanced_accuracy_score, r2_score

from mlsandbox.folds import FoldSet
from mlsandbox.methods import METHODS, build
from mlsandbox.missingness import inject_missing
from mlsandbox.results import Result, ResultStore

TIMEOUTS_BY_ROWS = ((500, 60), (10_000, 120), (float("inf"), 300))
"""Per-method budget in seconds, tiered by dataset size (FR-8.4). A flat cap generous for
300 rows fails every ensemble on 50,000."""

R2_FLOOR = 0.0
"""R² is floored so a catastrophic model cannot drag an average through large negative
values (D-021). Documented rather than silent."""


class Timeout(Exception):
    pass


def _raise_timeout(_signum, _frame):
    raise Timeout


def timeout_for(n_rows: int) -> int:
    return next(seconds for limit, seconds in TIMEOUTS_BY_ROWS if n_rows < limit)


def score_of(task: str, truth: np.ndarray, predicted: np.ndarray) -> float:
    """The study's metric (D-021).

    Balanced accuracy because the collection carries real imbalance, where plain accuracy
    would rank a majority-class predictor top. R² because regret averages across datasets,
    and an RMSE gap in house prices cannot be averaged with one in chemical concentration.
    """
    if task == "classification":
        return float(balanced_accuracy_score(truth, predicted))
    return max(float(r2_score(truth, predicted)), R2_FLOOR)


@dataclass
class Progress:
    """Live progress, because a run that shows nothing for six hours cannot be trusted or
    abandoned on the evidence it has already produced."""

    total: int
    done: int = 0
    skipped: int = 0
    failures: int = 0
    started: float = field(default_factory=time.perf_counter)

    def elapsed(self) -> float:
        return time.perf_counter() - self.started

    def eta_seconds(self) -> float | None:
        attempted = self.done - self.skipped
        if attempted < 3:
            return None
        rate = self.elapsed() / attempted
        return rate * (self.total - self.done)

    def line(self) -> str:
        parts = [f"{self.done}/{self.total}", f"{self.elapsed() / 60:.1f}m elapsed"]
        eta = self.eta_seconds()
        if eta is not None:
            parts.append(f"~{eta / 60:.0f}m left")
        if self.skipped:
            parts.append(f"{self.skipped} already done")
        if self.failures:
            parts.append(f"{self.failures} failed")
        return " · ".join(parts)


def evaluate_fold(
    *,
    dataset: str,
    source: str,
    method: str,
    task: str,
    features: pd.DataFrame,
    target: np.ndarray,
    folds: FoldSet,
    fold_index: int,
    missing_rate: float,
    budget_seconds: int,
    seed: int,
) -> Result:
    """Fit one method on one fold and score it, or record why it did not.

    The timeout is a signal, not a watchdog thread: sequential execution makes that
    possible, and it interrupts the fit wherever it is rather than waiting for a
    checkpoint the library never reaches.
    """
    train, test = folds.folds[fold_index]
    base = dict(
        dataset=dataset,
        source=source,
        method=method,
        task=task,
        missing_rate=missing_rate,
        fold=fold_index,
        fold_origin=folds.origin,
    )

    started = time.perf_counter()
    previous = signal.signal(signal.SIGALRM, _raise_timeout)
    signal.alarm(budget_seconds)
    try:
        # Built inside the guard: an unknown method, or one whose estimator cannot be
        # constructed, is a recorded outcome like any other failure. Outside it, a single
        # bad name would end a run measured in hours.
        pipeline = build(method, task, seed=seed)  # type: ignore[arg-type]
        fitted = clone(pipeline).fit(features.iloc[train], target[train])
        predicted = fitted.predict(features.iloc[test])
        score = score_of(task, target[test], predicted)
    except Timeout:
        return Result(
            **base,
            status="timeout",
            fit_seconds=time.perf_counter() - started,
            detail=f"exceeded {budget_seconds}s",
        )
    except Exception as error:  # noqa: BLE001 — a failure is a recorded outcome
        return Result(
            **base,
            status="error",
            fit_seconds=time.perf_counter() - started,
            detail=f"{type(error).__name__}: {str(error).splitlines()[0][:120]}",
        )
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, previous)

    return Result(**base, status="ok", score=score, fit_seconds=time.perf_counter() - started)


def variants(
    features: pd.DataFrame, rates: tuple[float, ...], seed: int
) -> Iterator[tuple[float, pd.DataFrame]]:
    """The same dataset at each missingness rate (D-015).

    Rate 0 is the original frame, not an injection of nothing, so the comparison baseline
    is the data as it came rather than a copy that went through the same machinery.
    """
    yield 0.0, features
    for rate in sorted({r for r in rates if r > 0}):
        # target_column is set to a name no frame has: the target is passed separately
        # here, so every column in `features` is a predictor and all are eligible.
        yield rate, inject_missing(features, rate=rate, seed=seed, target_column="__none__")


def run_dataset(
    *,
    dataset: str,
    source: str,
    task: str,
    features: pd.DataFrame,
    target: np.ndarray,
    folds: FoldSet,
    rates: tuple[float, ...],
    seed: int,
    store: ResultStore,
    completed: set,
    progress: Progress,
    report: Callable[[str], None],
) -> None:
    """Evaluate every method, variant and fold for one dataset."""
    budget = timeout_for(len(features))
    methods = [
        name
        for name, method in METHODS.items()
        if method.supports(task) and method.implementation == "sklearn"  # type: ignore[arg-type]
    ]

    for rate, frame in variants(features, rates, seed):
        for method in methods:
            outcomes: list[str] = []
            for fold_index in range(folds.n_folds):
                if (dataset, method, rate, fold_index) in completed:
                    progress.done += 1
                    progress.skipped += 1
                    continue

                result = evaluate_fold(
                    dataset=dataset,
                    source=source,
                    method=method,
                    task=task,
                    features=frame,
                    target=target,
                    folds=folds,
                    fold_index=fold_index,
                    missing_rate=rate,
                    budget_seconds=budget,
                    seed=seed,
                )
                store.add(result)
                progress.done += 1
                if result.status != "ok":
                    progress.failures += 1
                outcomes.append(result.status)

            if outcomes:
                scored = [o for o in outcomes if o == "ok"]
                summary = f"{len(scored)}/{len(outcomes)} folds"
                if len(scored) < len(outcomes):
                    summary += (
                        f" ({outcomes.count('timeout')} timeout, "
                        f"{outcomes.count('error')} error)"
                    )
                report(f"  {dataset[:28]:28} miss={rate:<5} {method:18} {summary}")
                store.flush()
