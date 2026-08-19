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
from mlsandbox.curation import SMALL_BAND_MAX_ROWS, Excluded, coverage, screen, stratified_sample
from mlsandbox.dataset import Dataset
from mlsandbox.missingness import RATES as MISSINGNESS_RATES
from mlsandbox.openml_source import load_metadata as load_openml_metadata
from mlsandbox.pmlb_source import (
    PINNED_REVISION,
    fetch_provenance,
    fetch_summary,
    load_dataset,
)

MANIFEST_PATH = PROJECT_ROOT / "config" / "collection.json"

PER_STRATUM = 10
"""Datasets kept per size-band x task-type cell. Six cells gives roughly 60 datasets:
enough rows to train Layer 2 on, and small enough to re-run the benchmark in an evening
when a bug appears (D-011)."""

MAX_PER_FAMILY = 2
"""PMLB carries large families from one source (`fri_c*`, `analcatdata_*`). Two per family
keeps some within-family variation without letting one kind of data dominate a band."""


def gather(config) -> tuple[list[Dataset], list[Excluded]]:
    """Combine the sources, each used where it is strong (D-025).

    OpenML's curated suites cover 500 rows and above, with predefined splits, a licence
    per dataset and eleven datasets carrying real missing values. PMLB supplies the band
    below that, which CC18 excludes by construction — its generator labels anything under
    500 rows `Too small`.

    PMLB is restricted to that band deliberately. Above it the two sources would overlap,
    and the same dataset could enter twice under different names with different
    provenance.
    """
    datasets = list(load_openml_metadata(config))

    out_of_band = []
    for dataset in fetch_summary(config):
        if dataset.rows < SMALL_BAND_MAX_ROWS:
            datasets.append(dataset)
        else:
            out_of_band.append(
                Excluded(
                    name=dataset.name,
                    reason=(
                        f"pmlb supplies the sub-{SMALL_BAND_MAX_ROWS}-row band only; "
                        "OpenML covers this size with better provenance (D-025)"
                    ),
                )
            )
    return datasets, out_of_band


FIELD_DOCS = {
    "sources": (
        "Each source and the band it covers. OpenML's curated suites carry provenance and "
        "predefined splits from 500 rows up; PMLB supplies the band below, which CC18 "
        "excludes by construction (D-025)."
    ),
    "pmlb_revision": (
        "The exact PMLB commit. Pinned, not a branch: a branch moves, and two runs months "
        "apart would draw on different collections. OpenML datasets carry their own "
        "version in `revision`."
    ),
    "seed": "Seed for the stratified sample. The same seed reproduces the same selection.",
    "max_per_family": (
        "Cap per dataset family. PMLB carries large families from one source (fri_c*, "
        "analcatdata_*); without a cap one kind of data would dominate a band."
    ),
    "per_stratum": (
        "Datasets kept per size-band x task-type cell. Six cells, so roughly six times "
        "this number survive."
    ),
    "counts.considered": "Every dataset in the source at this revision.",
    "counts.eligible": "Passed the selection rules, before sampling.",
    "counts.kept": "Survived the stratified sample. These are what the study runs on.",
    "counts.excluded": "Everything not kept, each with a reason. Nothing disappears silently.",
    "missingness_rates": (
        "Fractions of predictor cells blanked at evaluation time (D-015). The source "
        "ships pre-cleaned data, so the recommender's missing-value heuristic would "
        "otherwise go untested."
    ),
    "coverage": (
        "How many kept datasets exercise each characteristic the recommender reasons "
        "about. Zeros are shown rather than omitted: an invisible empty band is a claim "
        "the study cannot support."
    ),
    "datasets": "The collection the study runs on.",
    "datasets[].name": "Identifier within the source.",
    "datasets[].source": "Which collection this came from — a mixed set must explain itself.",
    "datasets[].revision": (
        "The exact version fetched: a dataset version for OpenML, the pinned commit for "
        "PMLB. What makes a re-run read identical bytes."
    ),
    "datasets[].licence": (
        "Terms the dataset is published under. `null` means unreported, which is not the "
        "same as unrestricted. Every OpenML dataset states one; PMLB states none."
    ),
    "datasets[].origin": "URL to follow the evidence back past this study.",
    "datasets[].rows": "Observations.",
    "datasets[].predictors": (
        "Feature columns actually present, excluding the target. Taken from the data "
        "rather than the index: OpenML counts row-identifier and ignored attributes that "
        "the loader drops."
    ),
    "datasets[].predictor_count_corrected_from": (
        "Present only where the index over-counted, recording what it claimed. The data "
        "is the truth; this keeps the disagreement visible instead of absorbing it."
    ),
    "datasets[].task": (
        "classification or regression, as the source states it. Carried explicitly "
        "because it cannot be derived from `classes`: the source does not zero that "
        "field for regression, and inferring from it files every regression dataset as "
        "classification."
    ),
    "datasets[].classes": (
        "Distinct target values. Only meaningful for classification — regression "
        "datasets also carry a value here."
    ),
    "datasets[].categorical_predictors": "Feature columns that are categorical.",
    "datasets[].missing_values": (
        "null means the source does not report it, which is not the same as zero. PMLB "
        "publishes no such column because its data is pre-cleaned; hence the injected "
        "rates above."
    ),
    "datasets[].imbalance": (
        "How far class proportions sit from equal: 0 is a perfect split, 0.94 is the "
        "most skewed present. Only meaningful for classification, though the source "
        "populates it for regression too."
    ),
    "excluded": (
        "Every dataset considered and not kept, with why. A collection whose gaps cannot "
        "be explained invites the suspicion that datasets were chosen to flatter the "
        "heuristics."
    ),
    "datasets[].provenance": (
        "Where the dataset came from before PMLB: original source URLs, the publication "
        "it accompanied, and PMLB's description. Required before republishing anything "
        "under D-010, since licences vary by original source."
    ),
    "datasets[].keywords": (
        "PMLB's own tags. `synthetic` and `simulation` exclude a dataset: the tag is "
        "authoritative where guessing from names is not."
    ),
    "excluded[].name": "Identifier of the excluded dataset.",
    "excluded[].reason": (
        "Why this dataset is absent: out of the product's scope, synthetic, deprecated "
        "by the source, or eligible but not sampled."
    ),
    "fetch_failures": (
        "Datasets that could not be downloaded or whose shape disagreed with the index. "
        "Recorded rather than raised, so one bad entry does not cost the whole run."
    ),
}


def build(datasets: list[Dataset], *, seed: int, config, pre_excluded=()) -> dict:
    screening = screen(datasets, max_per_family=MAX_PER_FAMILY)

    # PMLB tags synthetic datasets in their metadata. That tag is authoritative where
    # guessing from names is not: `529_pollen` is synthetic and matches no name pattern.
    eligible, tagged_synthetic, provenance = [], [], {}
    for dataset in screening.kept:
        # Only PMLB publishes the keyword tags; OpenML's suites are curated upstream.
        if dataset.source != "pmlb":
            eligible.append(dataset)
            continue
        record = fetch_provenance(dataset.name, config)
        if record is None:
            eligible.append(dataset)
            continue
        provenance[dataset.name] = record
        if record.is_synthetic:
            tagged_synthetic.append(
                Excluded(
                    name=dataset.name,
                    reason=(
                        "synthetic: tagged "
                        f"{sorted(set(record.keywords) & {'synthetic', 'simulation'})} "
                        "by the source"
                    ),
                )
            )
        else:
            eligible.append(dataset)

    sampled = stratified_sample(eligible, per_stratum=PER_STRATUM, seed=seed)
    return {
        "_fields": FIELD_DOCS,
        "sources": {
            "openml-cc18": "classification, 500 rows and above",
            "openml-ctr23": "regression, 500 rows and above",
            "pmlb": f"both tasks, under {SMALL_BAND_MAX_ROWS} rows",
        },
        "pmlb_revision": PINNED_REVISION,
        "seed": seed,
        "max_per_family": MAX_PER_FAMILY,
        "per_stratum": PER_STRATUM,
        "counts": {
            "considered": screening.total,
            "eligible": len(eligible),
            "kept": len(sampled.kept),
            "excluded": (
                len(pre_excluded)
                + len(screening.excluded)
                + len(tagged_synthetic)
                + len(sampled.excluded)
            ),
        },
        # PMLB ships pre-cleaned data, so the base collection cannot exercise the
        # recommender's missing-value heuristic. These rates are injected at evaluation
        # time to cover it as a controlled experiment (D-015).
        "missingness_rates": list(MISSINGNESS_RATES),
        "coverage": coverage(sampled.kept),
        "datasets": [
            {
                **d.model_dump(mode="json"),
                "provenance": (
                    provenance[d.name].model_dump(
                        mode="json", exclude={"name", "keywords"}
                    )
                    if d.name in provenance
                    else None
                ),
                "keywords": provenance[d.name].keywords if d.name in provenance else [],
            }
            for d in sampled.kept
        ],
        "excluded": [
            e.model_dump(mode="json")
            for e in list(pre_excluded) + screening.excluded + tagged_synthetic + sampled.excluded
        ],
    }


def report(manifest: dict) -> None:
    counts = manifest["counts"]
    print("sources: " + ", ".join(f"{k} ({v})" for k, v in manifest["sources"].items()))
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


def load_any(entry: dict, config):
    """Load a dataset whatever source it came from.

    The collection is mixed (D-025), so dispatching on source is not a nicety: calling
    PMLB's loader for an OpenML dataset would fail on every one of them.
    """
    if entry["source"] == "pmlb":
        return load_dataset(entry["name"], config)

    import openml

    from mlsandbox.openml_source import configure as configure_openml

    configure_openml(config)
    dataset_id = int(entry["origin"].rsplit("/", 1)[1])
    record = openml.datasets.get_dataset(dataset_id, download_data=True)
    frame, _, _, _ = record.get_data(dataset_format="dataframe")
    return frame


def fetch_all(manifest: dict, config) -> tuple[int, list[dict]]:
    """Download every selected dataset, recording rather than raising on failure.

    A dataset that cannot be retrieved is a documented exclusion, not a hole in the
    collection — and one bad name must not cost the other downloads.
    """
    fetched, failures = 0, []
    for entry in manifest["datasets"]:
        name = entry["name"]
        try:
            frame = load_any(entry, config)
        except Exception as error:  # noqa: BLE001 — every failure is recorded, not raised
            failures.append({"name": name, "reason": f"{type(error).__name__}: {error}"})
            continue

        # Rows are the hard invariant: a mismatch there means the wrong data.
        if frame.shape[0] != entry["rows"]:
            failures.append(
                {
                    "name": name,
                    "reason": (
                        f"{frame.shape[0]} rows on disk against {entry['rows']} in the index"
                    ),
                }
            )
            continue

        # Columns are not. OpenML counts row-identifier and ignored attributes in
        # NumberOfFeatures, and `get_data` drops them — so the index can legitimately
        # over-count. The data is the truth, so the manifest is corrected from it and the
        # discrepancy recorded rather than silently absorbed.
        actual_predictors = frame.shape[1] - 1
        if actual_predictors != entry["predictors"]:
            entry["predictor_count_corrected_from"] = entry["predictors"]
            entry["predictors"] = actual_predictors
        fetched += 1
    return fetched, failures


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="report without writing")
    parser.add_argument(
        "--fetch",
        action="store_true",
        help="download every selected dataset and record any that fail",
    )
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    config = load_config()

    datasets, out_of_band = gather(config)
    manifest = build(datasets, seed=config.run.seed, config=config, pre_excluded=out_of_band)
    report(manifest)

    if manifest["pmlb_revision"] == "master":
        print(
            "\nWARNING: revision is 'master', which moves. Pin a commit SHA before the "
            "final run or the study stops being reproducible."
        )

    if args.fetch:
        fetched, failures = fetch_all(manifest, config)
        print(f"\nfetched {fetched}/{len(manifest['datasets'])}")
        for failure in failures:
            print(f"  FAILED {failure['name']}: {failure['reason']}")
        manifest["fetch_failures"] = failures

    if not args.check:
        Path(MANIFEST_PATH).write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
        print(f"\nwritten to {MANIFEST_PATH.relative_to(PROJECT_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
