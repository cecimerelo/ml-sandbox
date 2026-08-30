"""Reading a user's CSV, and the rules for refusing one.

**Nothing here touches the filesystem.** FR-7.2 says uploaded datasets are processed in
memory and never written to disk, and the privacy notice will say so to a user. So the
functions take bytes rather than a path: there is no filename to write to, which makes the
promise a property of the signature rather than of everyone remembering.

Refusing well matters as much as parsing. A file rejected for one date column is a hostile
tool, and a file accepted with a target that cannot be predicted is a worse one — it
produces a model and a score and never says anything was wrong.
"""

from __future__ import annotations

import io
from typing import Literal

import pandas as pd

from mlsandbox.base import StrictModel

MAX_BYTES = 50 * 1024 * 1024
"""NFR-2's ceiling. Checked in the browser before the upload begins, so an oversized file
never crosses the wire, and again here because a client-side check is a courtesy rather
than a guarantee."""

MAX_FEATURES = 500
"""Checked on the header row, which is the first thing read and the cheapest thing to
refuse on."""

UNSUPPORTED = ("datetime64[ns]", "timedelta64[ns]")
"""Column types no method here accepts. Excluded from the feature set rather than being
grounds for rejection — see `read`."""

Refusal = Literal[
    "not-a-csv", "too-large", "too-many-features", "no-rows", "no-features", "all-unsupported"
]


class Rejected(StrictModel):
    """Why a file cannot be used, in words the user can act on."""

    reason: Refusal
    message: str


class Dataset(StrictModel):
    """A CSV that can be worked with, and what had to be left out of it."""

    columns: list[str]
    rows: int
    skipped: list[str] = []
    """Columns excluded because no method here can read them — dates, free text.

    Named so the interface can say which. Rejecting a whole file over one date column
    would be hostile, and silently dropping it would be worse: the user would wonder where
    their column went.
    """

    frame: object

    model_config = {"arbitrary_types_allowed": True, "frozen": True}


def _reject(reason: Refusal, message: str) -> Rejected:
    return Rejected(reason=reason, message=message)


def read(content: bytes, *, filename: str = "") -> Dataset | Rejected:
    """Parse an uploaded CSV from memory.

    Takes bytes, never a path. The privacy claim is then structural: there is nothing here
    that could write the file down even by mistake.
    """
    if len(content) > MAX_BYTES:
        megabytes = len(content) / 1024 / 1024
        return _reject(
            "too-large",
            f"This file is {megabytes:.0f} MB. The limit is {MAX_BYTES // 1024 // 1024} MB.",
        )

    if filename and not filename.lower().endswith(".csv"):
        return _reject(
            "not-a-csv",
            "This file isn't a CSV we can read. Upload a comma-separated file with a "
            "header row.",
        )

    try:
        frame = pd.read_csv(io.BytesIO(content))
    except Exception:  # noqa: BLE001 — every parse failure is the same message to a user
        return _reject(
            "not-a-csv",
            "This file isn't a CSV we can read. Upload a comma-separated file with a "
            "header row.",
        )

    if len(frame.columns) > MAX_FEATURES:
        return _reject(
            "too-many-features",
            f"This file has {len(frame.columns)} columns. The limit is {MAX_FEATURES}.",
        )

    if frame.empty:
        return _reject("no-rows", "This file has a header row but no data.")

    if len(frame.columns) < 2:
        return _reject(
            "no-features", "This file has only one column, so there's nothing to predict from."
        )

    # Dates and free text are excluded, not fatal. A whole file refused over one date
    # column is a tool that makes the user do the work it exists to save them.
    skipped = [column for column in frame.columns if _is_unsupported(frame[column])]
    kept = [column for column in frame.columns if column not in skipped]
    if not kept:
        return _reject(
            "all-unsupported",
            "None of these columns can be used yet — they're all dates or free text.",
        )

    return Dataset(
        columns=kept, rows=len(frame), skipped=skipped, frame=frame[kept]
    )


def _is_unsupported(column: pd.Series) -> bool:
    """Dates, and text that is not a category.

    Free text is judged by how repetitive it is: a column where nearly every value is
    different is a note or an identifier, not something to learn from. A column of city
    names repeats, and is kept.
    """
    if str(column.dtype) in UNSUPPORTED:
        return True
    if pd.api.types.is_numeric_dtype(column):
        return False
    distinct = column.nunique(dropna=True)
    return bool(len(column)) and distinct / len(column) > 0.9
