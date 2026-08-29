"""Where benchmark results are written, and how a run resumes.

One row per (dataset, method, missingness rate, fold). The fold-level grain is not
bookkeeping: the 1-standard-deviation tie rule runs through the ranking, the early halt
and the interface, and a standard deviation cannot be recovered from a mean. Storing
aggregates would quietly remove that rule from the study.

Written incrementally so an interrupted run resumes instead of restarting — a full run is
hours, and losing it to a crash at hour five is a cost worth engineering away.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Literal

import pandas as pd

from mlsandbox.base import StrictModel

Status = Literal["ok", "timeout", "error"]


class Result(StrictModel):
    """One fold of one method on one variant of one dataset."""

    dataset: str
    source: str
    method: str
    task: str
    missing_rate: float
    fold: int
    fold_origin: str
    """`openml` or `generated` — which partition this was scored on (D-003)."""

    status: Status
    score: float | None = None
    """None unless `status` is `ok`. A timeout is a recorded outcome, not a zero: scoring
    it as zero would let a slow method look worse than a bad one."""

    fit_seconds: float | None = None
    detail: str | None = None
    """Why, when the status is not `ok`."""

    @property
    def key(self) -> tuple[str, str, float, int]:
        return (self.dataset, self.method, self.missing_rate, self.fold)


def run_key(config_values: dict) -> str:
    """A short fingerprint of the settings a result depends on.

    Results from different seeds or fold counts are not interchangeable, and mixing them
    is invisible — the table looks complete either way. Keying the store on the settings
    makes a changed configuration start a new file rather than silently contaminating the
    old one.
    """
    payload = json.dumps(config_values, sort_keys=True).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()[:12]


class ResultStore:
    """Append-only result storage for one configuration."""

    def __init__(self, directory: Path, key: str) -> None:
        self.path = directory / f"results-{key}.parquet"
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._pending: list[dict] = []

    def completed(self) -> set[tuple[str, str, float, int]]:
        """What is already recorded, so a resumed run can skip it.

        Errors and timeouts count as completed: re-running them would spend the same time
        to reach the same outcome. Deleting the file is how you ask for a retry.
        """
        if not self.path.exists():
            return set()
        frame = pd.read_parquet(self.path)
        return set(
            zip(
                frame["dataset"],
                frame["method"],
                frame["missing_rate"],
                frame["fold"],
                strict=True,
            )
        )

    def add(self, result: Result) -> None:
        self._pending.append(result.model_dump(mode="json"))

    def flush(self) -> int:
        """Write buffered rows to disk.

        Called often rather than once at the end: the point of incremental writing is that
        an interruption costs the last few results, not the whole run.
        """
        if not self._pending:
            return 0
        frame = pd.DataFrame(self._pending)
        if self.path.exists():
            frame = pd.concat([pd.read_parquet(self.path), frame], ignore_index=True)
        frame.to_parquet(self.path, index=False)
        written = len(self._pending)
        self._pending.clear()
        return written

    def load(self) -> pd.DataFrame:
        return pd.read_parquet(self.path) if self.path.exists() else pd.DataFrame()


def store_for(config, *, rates, methods) -> ResultStore:
    """The store a run with these settings reads and writes.

    Here rather than in the script that runs the benchmark, because a second caller — the
    one that reports the metrics — has to reach the same file, and computing the key in two
    places means computing it two ways. That already happened: the reporting script left
    out the rates and the method list, looked for a file that had never existed, and
    announced there were no results while fourteen thousand of them sat on disk.
    """
    return ResultStore(
        config.paths.datasets.parent / "results",
        run_key(
            {
                "seed": config.run.seed,
                "n_folds": config.cv.n_folds,
                "rates": sorted(rates),
                "methods": sorted(methods),
            }
        ),
    )
