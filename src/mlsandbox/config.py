"""Configuration loading and seed handling.

A run of the study is fully defined by this config plus the seed inside it. Two runs
with the same config must produce identical results — the thesis claims
reproducibility, so anything that breaks that is a bug.

Values are validated at load time rather than trusted, because a mistyped TOML entry
should fail here, loudly, instead of surfacing as a strange number in a result table
hours later.
"""

from __future__ import annotations

import random
import tomllib
from pathlib import Path
from typing import Self

import numpy as np
from pydantic import Field, model_validator

from mlsandbox.base import StrictModel

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG_PATH = PROJECT_ROOT / "config" / "benchmark.toml"


class RunConfig(StrictModel):
    seed: int


class CVConfig(StrictModel):
    n_folds: int = Field(ge=2)


class PathsConfig(StrictModel):
    datasets: Path
    """Where the study's datasets live once fetched.

    Not a cache in the disposable sense: these are the exact data the results are computed
    on, and re-fetching them depends on an external service still serving the same bytes.
    """

    sessions: Path = Path("data/sessions.db")
    """Where anonymised session records live (FR-7.3).

    **A different kind of thing from everything else under `data/`.** The datasets and the
    results are study artifacts: reproducible, publishable, and safe to hand to anyone
    checking the work. This is a record of what people did, and it is neither. It is
    gitignored like the rest, but for a different reason — not because it is large, because
    it is not ours to publish.

    Kept out of `datasets.parent` on purpose, so nothing that sweeps the study's outputs
    picks it up by accident.
    """

    @model_validator(mode="after")
    def resolve_against_project_root(self) -> Self:
        # Paths in the TOML are relative so the config stays portable; everything
        # downstream wants them absolute.
        updates = {
            field: PROJECT_ROOT / value
            for field, value in ((f, getattr(self, f)) for f in ("datasets", "sessions"))
            if not value.is_absolute()
        }
        return self.model_copy(update=updates) if updates else self


class Config(StrictModel):
    run: RunConfig
    cv: CVConfig
    paths: PathsConfig


def load_config(path: Path | None = None) -> Config:
    config_path = path or DEFAULT_CONFIG_PATH
    with config_path.open("rb") as handle:
        return Config.model_validate(tomllib.load(handle))


def seed_everything(seed: int) -> None:
    """Seed the global RNGs the study can reach.

    This only covers libraries that fall back to a global generator. Any estimator
    accepting an explicit `random_state` must still be given one — relying on global
    state for those is how a run quietly stops being reproducible.
    """
    random.seed(seed)
    np.random.seed(seed)
