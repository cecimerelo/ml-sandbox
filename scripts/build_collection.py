"""Select the benchmark collection and write its manifest.

The manifest is the study's record of what it drew conclusions from: which datasets went
in, which did not, and why. It is committed to the repository, because a selection nobody
can inspect is a selection nobody can trust.

    uv run python scripts/build_collection.py           # write the manifest
    uv run python scripts/build_collection.py --check    # report without writing
"""

from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path

from mlsandbox.config import PROJECT_ROOT, load_config
from mlsandbox.curation import coverage, screen, stratified_sample
from mlsandbox.dataset import Dataset
from mlsandbox.missingness import RATES as MISSINGNESS_RATES
from mlsandbox.pmlb_source import PINNED_REVISION, fetch_summary

MANIFEST_PATH = PROJECT_ROOT / "config" / "collection.json"

PER_STRATUM = 10
"""Datasets kept per size-band x task-type cell. Six cells gives roughly 60 datasets:
enough rows to train Layer 2 on, and small enough to re-run the benchmark in an evening
when a bug appears (D-011)."""

MAX_PER_FAMILY = 2
"""PMLB carries large families from one source (`fri_c*`, `analcatdata_*`). Two per family
keeps some within-family variation without letting one kind of data dominate a band."""


def build(datasets: list[Dataset], *, seed: int) -> dict:
    screening = screen(datasets, max_per_family=MAX_PER_FAMILY)
    sampled = stratified_sample(screening.kept, per_stratum=PER_STRATUM, seed=seed)
    return {
        "source": "pmlb",
        "revision": PINNED_REVISION,
        "seed": seed,
        "max_per_family": MAX_PER_FAMILY,
        "per_stratum": PER_STRATUM,
        "counts": {
            "considered": screening.total,
            "eligible": len(screening.kept),
            "kept": len(sampled.kept),
            "excluded": len(screening.excluded) + len(sampled.excluded),
        },
        # PMLB ships pre-cleaned data, so the base collection cannot exercise the
        # recommender's missing-value heuristic. These rates are injected at evaluation
        # time to cover it as a controlled experiment (D-015).
        "missingness_rates": list(MISSINGNESS_RATES),
        "coverage": coverage(sampled.kept),
        "datasets": [d.model_dump(mode="json") for d in sampled.kept],
        "excluded": [
            e.model_dump(mode="json") for e in screening.excluded + sampled.excluded
        ],
    }


def report(manifest: dict) -> None:
    counts = manifest["counts"]
    print(f"source {manifest['source']} @ {manifest['revision']}")
    print(
        f"considered {counts['considered']} · eligible {counts['eligible']} "
        f"· sampled {counts['kept']}"
    )
    print("\ncoverage")
    for band, count in manifest["coverage"].items():
        flag = "  <-- EMPTY" if count == 0 else ""
        if band == "has missing values" and count == 0:
            flag = f"  <-- none in source; injected at {MISSINGNESS_RATES} (D-015)"
        print(f"  {band:34} {count:>4}{flag}")

    reasons: dict[str, int] = {}
    for entry in manifest["excluded"]:
        key = entry["reason"].split(":")[0].split("(")[0].strip()
        reasons[key] = reasons.get(key, 0) + 1
    print("\nexclusions by reason")
    for reason, count in sorted(reasons.items(), key=lambda kv: -kv[1]):
        print(f"  {reason[:52]:52} {count:>4}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="report without writing")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    config = load_config()

    manifest = build(fetch_summary(config), seed=config.run.seed)
    report(manifest)

    if manifest["revision"] == "master":
        print(
            "\nWARNING: revision is 'master', which moves. Pin a commit SHA before the "
            "final run or the study stops being reproducible."
        )

    if not args.check:
        Path(MANIFEST_PATH).write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
        print(f"\nwritten to {MANIFEST_PATH.relative_to(PROJECT_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
