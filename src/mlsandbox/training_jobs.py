"""What a live training run is, and where it lives between requests (#80, D-053).

The same split as `results.py`/`benchmark.py`: that module owns the record of one
offline evaluation and where it is stored, `benchmark.py` owns running the evaluation
that produces one. Here, `TrainingJob`/`MethodResult` are the record, and `training.py`
is what runs the methods that fill them in.

A `TrainingJob` is the only place a running job can be found again after the request
that started it has ended — a `multiprocessing.Process` and a background thread outlive
the HTTP request that spawned them, but nothing else does, so `register`/`get` are how
`GET /api/train/{id}` (#81) and #4.4/#4.5's chart endpoints reach the same object.
"""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field
from typing import Literal

from sklearn.pipeline import Pipeline

from mlsandbox.methods import Task

JOB_TTL_SECONDS = 60 * 60
"""How long a finished job's state, including its fitted pipelines, stays in memory
after `done` — long enough for #4.4/#4.5's charts to still be readable in the same
browser session, short enough that an abandoned tab does not hold a fitted model (and
the dataset it was trained on) forever. Nothing else bounds this: there is no session or
login to expire it on, so time since completion is the only signal available."""

MethodStatus = Literal["pending", "running", "ok", "timeout", "error", "stopped"]


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
    """In fit-score order, as decided by the caller (#4.2) — `training.py` trains them
    in the order given, it does not re-rank."""
    task: Task
    budget_seconds: int
    """The per-method timeout tier (FR-8.4), fixed once at job creation from the
    dataset's row count. Exposed to the frontend so its loading estimate — remaining
    methods times this — is computed from the one number the backend already decided,
    not a second copy of `TIMEOUTS_BY_ROWS` reimplemented in TypeScript."""
    results: dict[str, MethodResult] = field(default_factory=dict)
    current: str | None = None
    halted_early: bool = False
    stop_requested: bool = False
    aborted: bool = False
    abort_detail: str | None = None
    done: bool = False
    completed_at: float | None = None
    """`time.monotonic()` when `done` first became true — the eviction clock (`JOB_TTL_SECONDS`)
    reads from this, not wall-clock time, so a system clock change cannot extend or shorten
    a job's life."""
    _lock: threading.Lock = field(default_factory=threading.Lock, repr=False, compare=False)

    def snapshot(self) -> dict:
        """A read-only view for the polling endpoint (#4.2) — copied out from under the
        lock rather than handed the live dict, so a concurrent update mid-read cannot be
        observed half-written."""
        with self._lock:
            return {
                "id": self.id,
                "methods": list(self.methods),
                "budget_seconds": self.budget_seconds,
                "current": self.current,
                "halted_early": self.halted_early,
                "aborted": self.aborted,
                "abort_detail": self.abort_detail,
                "done": self.done,
                "results": dict(self.results),
            }

    def mark_done(self) -> None:
        """Every path that ends the run sets `done` through here, never by assigning the
        field directly — two invariants live here that a new exit path would otherwise
        have to remember separately: the completion timestamp `_sweep_expired` depends
        on, and `current` being cleared. Without the second, a job that ends early — an
        early halt, an aborted method, a stop — left `current` naming whichever method
        was running when it exited, and the frontend (which reads `current == method` as
        "still fitting", with priority over an already-`ok` result) showed that method
        spinning forever even though its result had already landed."""
        self.done = True
        self.completed_at = time.monotonic()
        self.current = None


_REGISTRY: dict[str, TrainingJob] = {}
_REGISTRY_LOCK = threading.Lock()


def _sweep_expired() -> None:
    """Drops jobs whose `JOB_TTL_SECONDS` has elapsed since they finished.

    Run opportunistically from `register`/`get` rather than on a timer: this app has no
    scheduler already running, and a job leaking a user's fitted models (and the data
    behind them) past its stated lifetime is worse than doing this check a little more
    often than strictly necessary.
    """
    now = time.monotonic()
    expired = [
        job_id
        for job_id, job in _REGISTRY.items()
        if job.completed_at is not None and now - job.completed_at > JOB_TTL_SECONDS
    ]
    for job_id in expired:
        del _REGISTRY[job_id]


def register(job: TrainingJob) -> None:
    with _REGISTRY_LOCK:
        _sweep_expired()
        _REGISTRY[job.id] = job


def get(job_id: str) -> TrainingJob | None:
    with _REGISTRY_LOCK:
        _sweep_expired()
        return _REGISTRY.get(job_id)
