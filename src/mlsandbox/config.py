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
from pydantic import BaseModel, ConfigDict, Field, model_validator

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG_PATH = PROJECT_ROOT / "config" / "benchmark.toml"


class StrictModel(BaseModel):
    """Rejects unknown keys and stays immutable once built.

    `extra="forbid"` matters more than it looks: a typo'd key would otherwise be
    silently ignored and the default used instead, which is exactly how a run
    produces plausible-looking wrong results.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)


class RunConfig(StrictModel):
    seed: int


class CVConfig(StrictModel):
    n_folds: int = Field(ge=2)


class PathsConfig(StrictModel):
    cache: Path

    @model_validator(mode="after")
    def resolve_against_project_root(self) -> Self:
        # Paths in the TOML are relative so the config stays portable; everything
        # downstream wants them absolute.
        if not self.cache.is_absolute():
            return self.model_copy(update={"cache": PROJECT_ROOT / self.cache})
        return self


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
