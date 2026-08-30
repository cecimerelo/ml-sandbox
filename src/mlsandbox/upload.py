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

DATE_SAMPLE = 50
"""How many values to try parsing as dates before deciding.

A CSV has no types: `read_csv` hands back `2024-01-01` as a string, so a date column looks
exactly like text unless someone tries. Sampled rather than parsed in full, because the
answer is the same after fifty rows and the cost is not."""

DATE_SHARE = 0.9
"""How much of the sample must parse. Below this it is text that happens to contain a few
dates, which is a different thing and should be described as one."""

Refusal = Literal[
    "not-a-csv", "too-large", "too-many-features", "no-rows", "no-features", "all-unsupported"
]

SkipReason = Literal["date", "free-text"]


class Skipped(StrictModel):
    """A column that cannot be used, and why — in the words a user is shown.

    The reason travels with the column because the interface shows these **disabled rather
    than hidden**, the same rule FR-8.3 sets for methods that do not apply. A column that
    silently vanishes leaves someone hunting for it, and teaches them nothing; one shown
    greyed out with a reason answers the question before it is asked.
    """

    column: str
    reason: SkipReason
    message: str


class Rejected(StrictModel):
    """Why a file cannot be used, in words the user can act on."""

    reason: Refusal
    message: str


class Dataset(StrictModel):
    """A CSV that can be worked with, and what had to be left out of it."""

    columns: list[str]
    rows: int
    skipped: list[Skipped] = []
    """Columns excluded because no method here can read them, each with its reason.

    Rejecting a whole file over one date column would be hostile, and silently dropping it
    would be worse: the user would wonder where their column went. Shown disabled with the
    reason instead.
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
    skipped = [
        note for column in frame.columns if (note := _unsupported(frame[column], column))
    ]
    excluded = {note.column for note in skipped}
    kept = [column for column in frame.columns if column not in excluded]
    if not kept:
        return _reject(
            "all-unsupported",
            "None of these columns can be used yet — they're all dates or free text.",
        )

    return Dataset(
        columns=kept, rows=len(frame), skipped=skipped, frame=frame[kept]
    )


def _unsupported(values: pd.Series, name: str) -> Skipped | None:
    """Why this column cannot be used, or `None` if it can.

    Free text is told from labels by how repetitive it is: a column where nearly every
    value is different is a note or a reference, not something to learn from. A column of
    city names repeats, and is kept.
    """
    if str(values.dtype) in UNSUPPORTED or _reads_as_dates(values):
        return Skipped(
            column=name,
            reason="date",
            message="Dates aren't supported yet — we can't tell what to do with them.",
        )
    if pd.api.types.is_numeric_dtype(values):
        return None
    if len(values) and values.nunique(dropna=True) / len(values) > 0.9:
        return Skipped(
            column=name,
            reason="free-text",
            message=(
                "Almost every row here is different, so this reads as free text or a "
                "reference number rather than something to learn from."
            ),
        )
    return None


def _reads_as_dates(values: pd.Series) -> bool:
    """Whether a text column is really dates.

    Checked before the free-text rule, because dates are also nearly all distinct and would
    otherwise be reported as notes — a message that is wrong about the user's data in a way
    they can see, which is worse than saying nothing.
    """
    sample = values.dropna().head(DATE_SAMPLE)
    if sample.empty or pd.api.types.is_numeric_dtype(sample):
        return False
    parsed = pd.to_datetime(sample, errors="coerce", format="mixed")
    return bool(parsed.notna().mean() >= DATE_SHARE)
