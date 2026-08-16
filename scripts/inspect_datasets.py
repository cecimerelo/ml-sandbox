"""Inspect candidate OpenML datasets by id.

Curation aid, not part of the study: it reports what a set of candidate datasets
actually contains so the selection can be made on facts rather than on the web UI's
facet counts, which are not intersection counts and have been observed to contradict
themselves.

    uv run python scripts/inspect_datasets.py 31 50 1504
"""

from __future__ import annotations

import logging
import sys

from mlsandbox.config import load_config
from mlsandbox.openml_client import DatasetMetadata, FetchFailure, configure, fetch_metadata

SMALL_BAND_MAX_ROWS = 500
"""FR-1.3's lowest band. Datasets at or above this are already covered by the curated
suites, so a candidate here only earns its place below it."""

MAX_FEATURES = 500
"""NFR-2."""


def main(dataset_ids: list[int]) -> int:
    logging.basicConfig(level=logging.WARNING, format="%(levelname)s %(message)s")
    configure(load_config())

    found: list[DatasetMetadata] = []
    failed: list[FetchFailure] = []

    for dataset_id in dataset_ids:
        result = fetch_metadata(dataset_id)
        if isinstance(result, FetchFailure):
            failed.append(result)
        else:
            found.append(result)

    header = (
        f"{'id':>6}  {'name':32} {'rows':>7} {'cols':>6} "
        f"{'classes':>8} {'missing':>8} {'categ':>6}  notes"
    )
    print(header)
    print("-" * len(header))
    for meta in found:
        notes = []
        if meta.rows >= SMALL_BAND_MAX_ROWS:
            notes.append(f"rows>={SMALL_BAND_MAX_ROWS}: outside the gap we are filling")
        if meta.features > MAX_FEATURES:
            notes.append("exceeds NFR-2 feature cap")
        if meta.classes == 0:
            notes.append("regression")
        elif meta.classes > 2:
            notes.append(f"multiclass ({meta.classes})")
        if meta.missing_values:
            notes.append("has missing values")
        if meta.categorical_features > 1:
            notes.append("has categorical features")

        print(
            f"{meta.dataset_id:>6}  {meta.name[:32]:32} {meta.rows:>7} {meta.features:>6} "
            f"{meta.classes:>8} {meta.missing_values:>8} {meta.categorical_features:>6}  "
            + "; ".join(notes)
        )

    for failure in failed:
        print(f"{failure.dataset_id:>6}  UNAVAILABLE — {failure.reason}")

    print(f"\nfetched {len(found)}/{len(dataset_ids)}")
    if found:
        usable = [
            m for m in found if m.rows < SMALL_BAND_MAX_ROWS and m.features <= MAX_FEATURES
        ]
        print(f"within the sub-{SMALL_BAND_MAX_ROWS}-row band and feature cap: {len(usable)}")
    return 0 if found else 1


if __name__ == "__main__":
    raise SystemExit(main([int(arg) for arg in sys.argv[1:]]))
