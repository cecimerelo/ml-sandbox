"""The benchmark collection, sourced from PMLB.

PMLB replaced OpenML as the primary source after a documented, recurring API outage
(D-013). The practical difference is availability: PMLB's datasets live in a GitHub
repository, so fetching them follows GitHub's uptime rather than a research server's.

It also covers the sub-500-row band natively — 146 datasets — which CC18 excludes by
construction. That is the gap that made D-006's subsampling necessary; with PMLB,
subsampling survives only as the controlled bias-variance experiment.
"""

from __future__ import annotations

import csv
import io
import logging
from pathlib import Path

import pandas as pd
import requests

from mlsandbox.config import Config
from mlsandbox.dataset import Dataset

logger = logging.getLogger(__name__)

SUMMARY_URL = (
    "https://raw.githubusercontent.com/EpistasisLab/pmlb/master/pmlb/all_summary_stats.tsv"
)
"""The collection's index. Pinning `master` is provisional — see `PINNED_REVISION`."""

PINNED_REVISION = "7c1f4bdc00136dc2e55c87fa6b8ba6e8af6d1a68"
"""PMLB at 2025-02-25 ("First principles datasets", #181).

A commit SHA, not a branch. `master` moves, so two runs months apart could draw on
different collections and the study would quietly stop being reproducible. Pinning is the
whole reproducibility advantage PMLB has over OpenML's dataset versioning.

Changing this invalidates the manifest: re-run `scripts/build_collection.py --fetch`, and
expect the selection to differ if datasets were added or withdrawn.
"""


def _summary_url(revision: str = PINNED_REVISION) -> str:
    return SUMMARY_URL.replace("/master/", f"/{revision}/")


def parse_summary(text: str) -> list[Dataset]:
    """Parse PMLB's summary table from its raw text.

    Kept separate from fetching so the parse can be exercised on a string, with no disk
    and no network involved.
    """
    return [_parse_row(row) for row in csv.DictReader(io.StringIO(text), delimiter="\t")]


def fetch_summary(config: Config, *, revision: str = PINNED_REVISION) -> list[Dataset]:
    """Load PMLB's summary table, from disk when it is already there.

    Small (~32KB), but keeping it on disk is what makes a re-run independent of the
    network — the property D-008 exists for, and the reason today's OpenML outage would
    have been harmless.
    """
    index_path = config.paths.datasets / "pmlb" / f"summary-{revision}.tsv"
    index_path.parent.mkdir(parents=True, exist_ok=True)

    if index_path.exists():
        text = index_path.read_text(encoding="utf-8")
    else:
        logger.info("Fetching PMLB summary at revision %s", revision)
        response = requests.get(_summary_url(revision), timeout=60)
        response.raise_for_status()
        text = response.text
        index_path.write_text(text, encoding="utf-8")

    return parse_summary(text)


def _parse_row(row: dict[str, str], revision: str = PINNED_REVISION) -> Dataset:
    def number(key: str) -> float:
        raw = row.get(key) or 0
        try:
            return float(raw)
        except ValueError:
            return 0.0

    return Dataset(
        name=row["dataset"],
        source="pmlb",
        revision=revision,
        rows=int(number("n_instances")),
        # PMLB's n_features already excludes the target, unlike OpenML's.
        predictors=int(number("n_features")),
        task=row.get("task", ""),
        classes=int(number("n_classes")),
        categorical_predictors=int(number("n_categorical_features")),
        # PMLB reports no missing-value count: its datasets are pre-cleaned. None rather
        # than 0, because "not reported" and "none present" are different claims.
        missing_values=None,
        imbalance=number("imbalance"),
    )


def load_dataset(name: str, config: Config) -> pd.DataFrame:
    """Load one dataset, fetching it the first time.

    Deliberately not using the `pmlb` package's own fetcher: it stores files where it
    likes and resolves against whatever revision it shipped with, both of which undercut
    the pinning this module exists to guarantee.
    """
    # Scoped by revision: without it, changing PINNED_REVISION would silently reuse files
    # fetched under the old one, mixing two versions of the collection with no signal.
    store: Path = config.paths.datasets / "pmlb" / PINNED_REVISION
    store.mkdir(parents=True, exist_ok=True)
    local = store / f"{name}.tsv.gz"

    if not local.exists():
        # media.githubusercontent.com, not raw.: PMLB stores its datasets in Git LFS, and
        # the raw host returns the LFS pointer file rather than the data.
        url = (
            f"https://media.githubusercontent.com/media/EpistasisLab/pmlb/{PINNED_REVISION}"
            f"/datasets/{name}/{name}.tsv.gz"
        )
        logger.info("Fetching %s", name)
        response = requests.get(url, timeout=120)
        response.raise_for_status()
        local.write_bytes(response.content)

    return pd.read_csv(local, sep="\t", compression="gzip")
