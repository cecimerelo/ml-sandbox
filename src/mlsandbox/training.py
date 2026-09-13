"""Training the recommended methods on a user's own uploaded data, live (D-053, #80).

Every offline benchmark run is sequential in one process, timed with `signal.SIGALRM`
(`benchmark.py`) — a mechanism that only fires in a process's main thread, and cannot
force-kill anything. A live web request has neither guarantee: FastAPI runs a synchronous
endpoint in a threadpool worker, not the main thread, and FR-8.4's `Stop training` control
needs to actually stop a fit already in progress, not just decline to wait for it.

D-053's answer is to give up the signal entirely: each method fits inside its own
`multiprocessing.Process`, which the orchestrator can kill outright — on a timeout or on
`Stop` — because a subprocess, unlike a thread, can be terminated from outside it. The
per-method budget covers the whole method (every fold, plus the final fit below), not
each fold separately, because `join(timeout=...)` measures wall time for the process as a
whole; splitting it per fold would need N separate signals inside one subprocess, which is
exactly the mechanism this module exists to avoid.

Cross-validation itself is generated fresh per request via `folds.generate` — the same
function PMLB datasets already use in the offline study, since a user's own CSV has no
published partition to reuse (D-003's contract, extended rather than duplicated).
"""

from __future__ import annotations

import multiprocessing as mp
import threading
import time
import uuid
from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Literal

import numpy as np
import pandas as pd
from sklearn.pipeline import Pipeline

from mlsandbox import folds as foldslib
from mlsandbox.benchmark import score_of, timeout_for
from mlsandbox.methods import Task, build

POLL_INTERVAL_SECONDS = 0.5
"""How often the orchestrator checks a running subprocess for a Stop request or a
timeout. Coarser than this and Stop feels unresponsive; finer buys nothing — a fit is
not going to finish in the gap."""

MAX_FOLDS = 5
"""Matches the offline benchmark's fold count (D-003) as the ceiling; a small or
imbalanced dataset uses fewer, never more."""

MIN_CLASS_COUNT_FOR_CV = 2
"""Below this, no split can hold out even one example of the class and still leave one
to train on — there is no cross-validation to run, not merely a degraded one."""

MethodStatus = Literal["pending", "running", "ok", "timeout", "error", "stopped"]


class NotCrossValidatable(Exception):
    """Raised before any subprocess starts — the dataset's target has a class too small
    to hold out in any fold. A per-method failure would misattribute a property of the
    dataset to whichever method happened to run first."""


@dataclass
class MethodResult:
    method: str
    status: MethodStatus
    mean_score: float | None = None
    std_score: float | None = None
    fold_scores: list[float] = field(default_factory=list)
    fitted: Pipeline | None = None
    """The pipeline fit on the full dataset, present only when `status == "ok"` — what
    #4.4/#4.5's charts are drawn from. Not the cross-validated fold models: those exist
    only to score the method, never to explain it."""
    fit_seconds: float | None = None
    detail: str | None = None


@dataclass
class TrainingJob:
    id: str
    methods: list[str]
    """In fit-score order, as decided by the caller (#4.2) — this module trains them in
    the order given, it does not re-rank."""
    task: Task
    results: dict[str, MethodResult] = field(default_factory=dict)
    current: str | None = None
    halted_early: bool = False
    stop_requested: bool = False
    aborted: bool = False
    abort_detail: str | None = None
    done: bool = False
    _lock: threading.Lock = field(default_factory=threading.Lock, repr=False, compare=False)

    def snapshot(self) -> dict:
        """A read-only view for the polling endpoint (#4.2) — copied out from under the
        lock rather than handed the live dict, so a concurrent update mid-read cannot be
        observed half-written."""
        with self._lock:
            return {
                "id": self.id,
                "methods": list(self.methods),
                "current": self.current,
                "halted_early": self.halted_early,
                "aborted": self.aborted,
                "abort_detail": self.abort_detail,
                "done": self.done,
                "results": dict(self.results),
            }


def _n_folds_for(target: np.ndarray, task: Task) -> tuple[int, bool]:
    """How many folds, and whether they must be stratified.

    Adaptive rather than fixed: a fixed 5 fails outright on a dataset whose rarest class
    has 3 members. Capped at `MAX_FOLDS` rather than raised for a huge dataset — more
    folds buys precision on the standard deviation FR-8.4's halt rule reads, not on the
    score itself, and this module only ever explains a fit, it does not tune one.
    """
    if task == "regression":
        return MAX_FOLDS, False
    _, counts = np.unique(target, return_counts=True)
    smallest = int(counts.min())
    if smallest < MIN_CLASS_COUNT_FOR_CV:
        raise NotCrossValidatable(
            f"the rarest class has {smallest} example(s); at least "
            f"{MIN_CLASS_COUNT_FOR_CV} are needed to hold one out and still train on one"
        )
    return min(MAX_FOLDS, smallest), True


def _fit_worker(
    result_queue: mp.Queue,
    method: str,
    task: Task,
    features: pd.DataFrame,
    target: np.ndarray,
    n_folds: int,
    stratified: bool,
    seed: int,
) -> None:
    """Runs inside its own subprocess. Scores the method by cross-validation, then fits
    it once more on every row the user gave — the object #4.4/#4.5 render, not any one
    fold's model, which saw only part of the data and belongs to no chart.

    A top-level function, not a closure: `multiprocessing` on the `spawn` start method
    (macOS, Windows) can only hand a subprocess something importable by name.
    """
    try:
        fold_set = foldslib.generate(
            "live-upload", target=target, n_folds=n_folds, seed=seed, stratified=stratified
        )
        scores: list[float] = []
        for train_index, test_index in fold_set.folds:
            pipeline = build(method, task, seed=seed)
            pipeline.fit(features.iloc[train_index], target[train_index])
            predicted = pipeline.predict(features.iloc[test_index])
            scores.append(score_of(task, target[test_index], predicted))

        final = build(method, task, seed=seed)
        final.fit(features, target)
        result_queue.put(
            {
                "status": "ok",
                "fold_scores": scores,
                "mean_score": float(np.mean(scores)),
                "std_score": float(np.std(scores)),
                "fitted": final,
            }
        )
    except Exception as error:  # noqa: BLE001 — the outcome, not a crash, is what's reported
        detail = f"{type(error).__name__}: {str(error).splitlines()[0][:200]}"
        result_queue.put({"status": "error", "detail": detail})


def _run_one_method(
    job: TrainingJob,
    method: str,
    features: pd.DataFrame,
    target: np.ndarray,
    n_folds: int,
    stratified: bool,
    seed: int,
    budget_seconds: int,
    context: mp.context.BaseContext | None = None,
) -> MethodResult:
    """Starts the subprocess, then polls rather than making one blocking `join` call —
    `Stop training` and the timeout are otherwise indistinguishable from the outside, and
    both need to end the same process the same way.

    `context` defaults to the platform's own start method (D-053 leaves that choice
    alone — its cost is unmeasured, not a known problem). Tests pass `fork` explicitly:
    a forked child inherits the parent's already-patched module state, which lets a slow
    fake estimator stand in for a real slow fit; `spawn` re-imports from disk and would
    not see the patch at all.
    """
    ctx = context or mp
    started = time.perf_counter()
    queue = ctx.Queue()
    process = ctx.Process(
        target=_fit_worker,
        args=(queue, method, job.task, features, target, n_folds, stratified, seed),
    )
    process.start()

    while process.is_alive():
        process.join(timeout=POLL_INTERVAL_SECONDS)
        elapsed = time.perf_counter() - started
        with job._lock:
            stop_requested = job.stop_requested
        if stop_requested:
            process.terminate()
            process.join()
            return MethodResult(
                method=method, status="stopped", fit_seconds=elapsed, detail="stopped by request"
            )
        if elapsed > budget_seconds:
            process.terminate()
            process.join()
            return MethodResult(
                method=method,
                status="timeout",
                fit_seconds=elapsed,
                detail=f"exceeded {budget_seconds}s",
            )

    fit_seconds = time.perf_counter() - started
    if queue.empty():
        return MethodResult(
            method=method,
            status="error",
            fit_seconds=fit_seconds,
            detail="the training process exited without reporting a result",
        )
    outcome = queue.get()
    if outcome["status"] == "error":
        return MethodResult(
            method=method, status="error", fit_seconds=fit_seconds, detail=outcome["detail"]
        )
    return MethodResult(
        method=method,
        status="ok",
        mean_score=outcome["mean_score"],
        std_score=outcome["std_score"],
        fold_scores=outcome["fold_scores"],
        fitted=outcome["fitted"],
        fit_seconds=fit_seconds,
    )


def _should_halt_early(results: dict[str, MethodResult], order: Sequence[str]) -> bool:
    """FR-8.4: stop once the top 3 completed methods no longer distinguish themselves
    from the one currently leading.

    Compared against the leader's own standard deviation, not the three methods' average
    — the leader is the one the recommendation would show if training stopped right now,
    so "did the next two candidates actually beat its uncertainty" is the question that
    decides whether continuing could still change the answer.
    """
    completed = [
        results[name]
        for name in order
        if name in results and results[name].status == "ok"
    ]
    if len(completed) < 3:
        return False
    top_three = sorted(completed, key=lambda r: r.mean_score or 0.0, reverse=True)[:3]
    leader = top_three[0]
    spread = (leader.mean_score or 0.0) - (top_three[-1].mean_score or 0.0)
    return spread <= (leader.std_score or 0.0)


def _orchestrate(
    job: TrainingJob,
    features: pd.DataFrame,
    target: np.ndarray,
    seed: int,
    context: mp.context.BaseContext | None,
) -> None:
    try:
        n_folds, stratified = _n_folds_for(target, job.task)
    except NotCrossValidatable as error:
        with job._lock:
            job.aborted = True
            job.abort_detail = str(error)
            job.done = True
        return

    budget_seconds = timeout_for(len(features))

    for method in job.methods:
        with job._lock:
            if job.stop_requested:
                break
            job.current = method

        result = _run_one_method(
            job, method, features, target, n_folds, stratified, seed, budget_seconds, context
        )

        with job._lock:
            job.results[method] = result
            if result.status == "error":
                job.aborted = True
                job.abort_detail = f"{method}: {result.detail}"
                job.done = True
                return
            if _should_halt_early(job.results, job.methods):
                job.halted_early = True
                job.done = True
                return
            if result.status == "stopped":
                job.done = True
                return

    with job._lock:
        job.current = None
        job.done = True


def start(
    methods: list[str],
    task: Task,
    features: pd.DataFrame,
    target: np.ndarray,
    *,
    seed: int = 0,
    context: mp.context.BaseContext | None = None,
) -> TrainingJob:
    """Begins training `methods` (up to 5, in fit-score order) on the user's own data.

    Returns immediately with a `TrainingJob` whose fields update as the background
    thread progresses — the caller (#4.2's `POST /api/train`) hands its id back to the
    browser and lets `GET /api/train/{id}` read `job.snapshot()` from then on.

    Every requested method is assumed already restricted to `implementation == "sklearn"`
    (the same filter `benchmark.run_dataset` applies) — this module trusts its caller
    rather than re-deriving that filter, the way every other function here trusts the
    dataset it is handed rather than re-validating it.

    `context` is a `multiprocessing` start-method override for tests (see
    `_run_one_method`); production code leaves it at the platform default.
    """
    job = TrainingJob(id=str(uuid.uuid4()), methods=list(methods), task=task)
    thread = threading.Thread(
        target=_orchestrate, args=(job, features, target, seed, context), daemon=True
    )
    thread.start()
    return job


def request_stop(job: TrainingJob) -> None:
    with job._lock:
        job.stop_requested = True
