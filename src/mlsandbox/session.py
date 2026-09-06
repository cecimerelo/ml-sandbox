"""What one session records, and why so much care goes into what counts.

The product is also the instrument. Three of the thesis's metrics are read out of user
interactions, so **the interface must never manufacture the result the thesis is testing.**

The failure this exists to prevent is specific and was once filed as "not a gap". FR-8.4
auto-trains up to five methods ordered by fit score, and the recommended method is rank 1
by construction — so it is *always* trained. Any metric shaped like *"did the user run the
recommended method?"* reads 100% every session and measures nothing at all.

The fix is to distinguish what the system did from what the user chose, everywhere, and to
record the distinction rather than reconstruct it afterwards. It cannot be reconstructed:
a trained method leaves the same trace whichever way it got there.
"""

from __future__ import annotations

import json
import sqlite3
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal

from mlsandbox.base import StrictModel

RunOrigin = Literal["system", "user", "retry"]
"""How a training run started.

`system` — the user clicked `Get Recommendation` (or re-ran from stale). **Never a
deliberate selection, for any method in the batch, including the recommended one.**

`user` — the user toggled method chips on and ran a comparison. A deliberate selection, but
only for the chips they actually toggled in that run.

`retry` — `Try again` on a method that timed out. It inherits the origin of the run that
timed out rather than becoming a choice: a user rescuing a failed run has not decided
anything new.
"""

SelectorPath = Literal["promoted", "expander"]
"""Where a chosen method was picked from.

Three methods sit one click away and the rest are behind an accordion, so the selector is a
funnel. Recorded as a covariate rather than left as an invisible confound — otherwise a
method's popularity cannot be told apart from its position.
"""


class TrainedMethod(StrictModel):
    """One method that was actually trained, and how it came to be."""

    method: str
    origin: RunOrigin

    @property
    def is_deliberate(self) -> bool:
        """Whether running this counts as the user choosing it.

        Only `user`. The recommended method's chip is not deselectable (FR-5.2), so its
        presence in a comparison run is not evidence of choice and must never be counted
        as one.
        """
        return self.origin == "user"


class DeliberateSelection(StrictModel):
    """A method the user actively picked, and where they picked it from."""

    method: str
    selector: SelectorPath


class SessionRecord(StrictModel):
    """One anonymised session (FR-7.3).

    No dataset, no column names, no free text that could carry either. What is kept is
    what a decision was made from and what was decided.
    """

    session: str
    created: str

    drivers: dict[str, str]
    """The banded answers the recommendation was made from. Bands, never exact values —
    the same resolution the model was trained on, and none of it identifying."""

    named_interactions: int = 0
    """**How many** column pairs the user confirmed, never which.

    Column names from a private dataset are frequently identifying of the dataset and
    sometimes of its domain. Stored as a count so the analysis can ask whether interaction
    signal changes recommendations, without the record carrying anything that could name
    the data. Not hashed either: a hash of `patient_id` is still a stable identifier for
    `patient_id` (D-035)."""

    recommended: str
    promoted: list[str] = []
    """The three methods offered one click away. Half of the selector funnel."""

    trained: list[TrainedMethod] = []
    selections: list[DeliberateSelection] = []

    would_use: str | None = None
    """The FR-5.5 answer: which method the user says they would actually use.

    `None` means unanswered, and that is a real state rather than a missing value. The
    control is **never pre-filled and has no default** — pre-selecting the recommendation
    would fabricate the metric a second time, having already fabricated it once by
    auto-training the recommended method.
    """

    @property
    def accepted_explicitly(self) -> bool:
        """Arm A — the strong evidence. The user named the recommended method themselves."""
        return self.would_use == self.recommended

    @property
    def accepted_without_override(self) -> bool:
        """Arm B — the weak evidence. The session ended with no method named over it.

        Absence of an override is not the same as agreement: a user who never engaged with
        the alternatives looks identical to one who considered and kept the recommendation.
        Reported as its own figure and **never folded into Arm A**, which is why these are
        two properties and not one.
        """
        if self.would_use is not None:
            return self.would_use == self.recommended
        return all(s.method == self.recommended for s in self.selections)

    @property
    def deliberate_methods(self) -> list[str]:
        """What the user actually chose, for the diversity counter-metric.

        Auto-trained methods do not enter the count in either direction. Including them
        would measure what FR-8.4 picks, which is a property of the tool and not of anyone
        using it.
        """
        return sorted({s.method for s in self.selections})


def new_record(*, session: str, drivers: dict[str, str], recommended: str, **rest) -> SessionRecord:
    return SessionRecord(
        session=session,
        created=datetime.now(UTC).isoformat(timespec="seconds"),
        drivers=drivers,
        recommended=recommended,
        **rest,
    )


SCHEMA = """
CREATE TABLE IF NOT EXISTS sessions (
    session   TEXT PRIMARY KEY,
    created   TEXT NOT NULL,
    record    TEXT NOT NULL
)
"""


class SessionStore:
    """Anonymised session records, in SQLite.

    A few hundred rows, one per session (D-037). The record is kept as JSON rather than
    spread across columns because its shape will change as later epics add what they
    measure, and a migration per epic is a cost with no reader.
    """

    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as connection:
            connection.execute(SCHEMA)

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.path)

    def save(self, record: SessionRecord) -> None:
        """Write or replace one session.

        Replace rather than append: a session is edited as it goes — methods trained, then
        compared, then answered — and keeping every intermediate state would make the
        analysis count one session several times.
        """
        with self._connect() as connection:
            connection.execute(
                "INSERT OR REPLACE INTO sessions (session, created, record) VALUES (?, ?, ?)",
                (record.session, record.created, record.model_dump_json()),
            )

    def load(self, session: str) -> SessionRecord | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT record FROM sessions WHERE session = ?", (session,)
            ).fetchone()
        return SessionRecord(**json.loads(row[0])) if row else None

    def all(self) -> list[SessionRecord]:
        with self._connect() as connection:
            rows = connection.execute("SELECT record FROM sessions ORDER BY created").fetchall()
        return [SessionRecord(**json.loads(row[0])) for row in rows]


class Acceptance(StrictModel):
    """The acceptance metrics, as separate figures.

    A model rather than a dict of numbers so the two arms cannot be added together by
    accident. They measure different things: one is a person saying they would use the
    recommendation, the other is a person not saying otherwise, and the second is much
    weaker evidence. A single "acceptance rate" would be the more flattering of the two
    wearing the name of the stronger.
    """

    sessions: int
    explicit: float
    """Arm A — the user named the recommended method in the FR-5.5 control."""

    without_override: float
    """Arm B — the session ended with no other method named. Includes everyone who never
    engaged with the alternatives at all, which is why it is not evidence of agreement."""

    answered: int
    """How many sessions answered the prompt. Arm B's denominator includes those that did
    not, so this is what says how much of it rests on silence."""

    diversity: int
    """Distinct methods deliberately chosen across all sessions.

    The counter-metric: a recommender that always says the same thing can score well on
    acceptance while being useless, and this is what shows it."""


def summarise(records: list[SessionRecord]) -> Acceptance:
    if not records:
        return Acceptance(sessions=0, explicit=0.0, without_override=0.0, answered=0, diversity=0)

    chosen = {method for record in records for method in record.deliberate_methods}
    return Acceptance(
        sessions=len(records),
        explicit=sum(r.accepted_explicitly for r in records) / len(records),
        without_override=sum(r.accepted_without_override for r in records) / len(records),
        answered=sum(r.would_use is not None for r in records),
        diversity=len(chosen),
    )


def store_for(config) -> SessionStore:
    """The store this configuration writes to.

    Here rather than in whichever module first needs one, because a second caller computing
    the path its own way is how the benchmark ended up announcing there were no results
    while fourteen thousand sat on disk.
    """
    return SessionStore(config.paths.sessions)
