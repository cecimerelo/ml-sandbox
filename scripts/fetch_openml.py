"""Download the OpenML suites to disk, once, so the study never needs the service again.

OpenML's API has been unavailable for days at a time, with an upstream issue open since
July. The mitigation is not resilience at run time — it is not depending on the service at
run time (D-008). This script is the moment that dependency is paid off: run it while the
API answers, and every later run reads from disk.

    uv run python scripts/fetch_openml.py --metadata   # the suite index
    uv run python scripts/fetch_openml.py --data       # the datasets themselves
"""

from __future__ import annotations

import argparse
import json
import logging
import time

from mlsandbox.config import Config, load_config
from mlsandbox.curation import screen
from mlsandbox.dataset import Dataset
from mlsandbox.openml_source import SUITES, configure, fetch_suite

logger = logging.getLogger(__name__)

MAX_PER_FAMILY = 2
"""Matches the collection build, so this downloads what the study can actually select."""


def metadata_path(config: Config):
    return config.paths.datasets / "openml" / "suite-metadata.json"


def failures_path(config: Config):
    return config.paths.datasets / "openml" / "download-failures.json"


def fetch_metadata(config: Config) -> int:
    by_suite: dict[str, list[dict]] = {}
    for suite in SUITES:
        found, missing = fetch_suite(suite, config)
        print(f"{suite}: {len(found)} fetched, {len(missing)} unavailable", flush=True)
        by_suite[suite] = [d.model_dump(mode="json") for d in found]

    path = metadata_path(config)
    path.write_text(json.dumps(by_suite, indent=2) + "\n", encoding="utf-8")
    total = sum(len(v) for v in by_suite.values())
    print(f"\n{total} datasets described, written to {path.name}")
    return total


def load_metadata(config: Config) -> list[Dataset]:
    path = metadata_path(config)
    if not path.exists():
        raise SystemExit(f"{path.name} is missing — run with --metadata first")
    raw = json.loads(path.read_text(encoding="utf-8"))
    return [Dataset.model_validate(d) for suite in raw.values() for d in suite]


def fetch_data(config: Config) -> int:
    """Download the datasets that pass screening, smallest first.

    Smallest first on purpose: an interrupted run then leaves the most datasets usable,
    and a failure pattern shows up early rather than after the big ones have been fetched.
    """
    import openml

    configure(config)
    eligible = screen(load_metadata(config), max_per_family=MAX_PER_FAMILY).kept
    targets = sorted(
        ((int(d.origin.rsplit("/", 1)[1]), d.name, d.rows) for d in eligible if d.origin),
        key=lambda item: item[2],
    )

    fetched, failures = 0, []
    started = time.time()
    for index, (dataset_id, name, _rows) in enumerate(targets, start=1):
        try:
            record = openml.datasets.get_dataset(
                dataset_id, download_data=True, download_qualities=True
            )
            # Force the parse: a cached ARFF that cannot be read is not a backup.
            record.get_data(dataset_format="dataframe")
            fetched += 1
        except Exception as error:  # noqa: BLE001 — recorded, not raised
            failures.append(
                {
                    "id": dataset_id,
                    "name": name,
                    "reason": f"{type(error).__name__}: {str(error).splitlines()[0][:120]}",
                }
            )
        if index % 10 == 0:
            print(
                f"{index}/{len(targets)}  ok={fetched} failed={len(failures)}  "
                f"{time.time() - started:.0f}s",
                flush=True,
            )

    failures_path(config).write_text(json.dumps(failures, indent=2) + "\n", encoding="utf-8")
    print(f"\n{fetched} downloaded, {len(failures)} failed in {time.time() - started:.0f}s")
    for failure in failures:
        print(f"  FAILED {failure['name']}: {failure['reason']}")
    return len(failures)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--metadata", action="store_true", help="fetch the suite index")
    parser.add_argument("--data", action="store_true", help="fetch the datasets themselves")
    args = parser.parse_args()

    logging.basicConfig(level=logging.WARNING, format="%(levelname)s %(message)s")
    config = load_config()

    if not (args.metadata or args.data):
        parser.error("choose --metadata, --data, or both")
    if args.metadata:
        fetch_metadata(config)
    if args.data:
        return 1 if fetch_data(config) else 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
