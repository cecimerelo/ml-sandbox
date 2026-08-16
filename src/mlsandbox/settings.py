"""Secrets and environment-provided settings.

Kept apart from `config.py` on purpose: `config/benchmark.toml` holds the study's knobs
and belongs in version control, while this holds credentials and must never be
committed.
"""

from __future__ import annotations

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from mlsandbox.config import PROJECT_ROOT


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    openml_api_key: str = Field(default="", description="OpenML API key; see .env.example")


def load_settings() -> Settings:
    return Settings()
