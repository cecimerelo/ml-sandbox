"""Shared model base.

Validation is not ceremony here: this is a research pipeline, and a wrong value that
passes silently becomes a plausible-looking result nobody questions. Everything that
crosses a boundary — config, dataset metadata, selection outcomes — is validated at
construction.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class StrictModel(BaseModel):
    """Rejects unknown fields and stays immutable once built.

    `extra="forbid"` matters more than it looks: a typo'd key would otherwise be silently
    ignored and a default used in its place, which is exactly how a run produces results
    that look reasonable and are wrong.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)
