"""Run the benchmark.

    uv run python scripts/run_benchmark.py --sample 3    # a few datasets, ~a minute
    uv run python scripts/run_benchmark.py               # the full collection, hours

Sequential and resumable. Interrupt it whenever: the next run skips what is already
recorded, so stopping costs the fold in flight and nothing else.
"""

from __future__ import annotations

import argparse
import json
import logging
import time
import warnings

import numpy as np

from mlsandbox.benchmark import Progress, cap_rows, run_dataset
from mlsandbox.config import PROJECT_ROOT, load_config, seed_everything
from mlsandbox.folds import from_openml, generate
from mlsandbox.loading import load_any, split_target
from mlsandbox.methods import METHODS
from mlsandbox.missingness import RATES
from mlsandbox.openml_source import N_FOLDS, load_splits
from mlsandbox.openml_source import configure as configure_openml
from mlsandbox.results import ResultStore, run_key

warnings.filterwarnings("ignore")

MANIFEST = PROJECT_ROOT / "config" / "collection.json"


def report(message: str) -> None:
    """Print immediately.

    Explicit because the pilot ran fifteen minutes showing nothing: Python buffers stdout
    when it is not a terminal, and a long job you cannot watch is one you cannot abandon
    early on the evidence it has already produced.
    """
    print(message, flush=True)


def load_frame(entry: dict, config):
    features, target = split_target(load_any(entry, config))
    return features, target.to_numpy()


def folds_for(entry: dict, target: np.ndarray, config, task_ids: dict[str, int]):
    """Published splits where the source has them, generated ones otherwise (D-003).

    Falls back to generated folds when OpenML's are unreachable, and says so — a run that
    silently changes its partitioning would produce results that cannot be compared with
    the ones beside them.
    """
    name, task = entry["name"], entry["task"]
    if entry["source"].startswith("openml"):
        configure_openml(config)
        task_id = task_ids.get(name)
        if task_id is not None:
            splits = load_splits(task_id)
            if splits:
                return from_openml(name, splits)
        report(f"  ! {name}: OpenML splits unavailable, generating instead")

    return generate(
        name,
        target=target,
        n_folds=config.cv.n_folds,
        seed=config.run.seed,
        stratified=task == "classification",
    )


def expected_evaluations(entry: dict, generated_folds: int, n_rates: int) -> int:
    """How many fold evaluations this dataset will produce.

    The fold count differs by source — OpenML's tasks define ten, generated ones follow
    the config — so a single number here would make the total, and the ETA built on it,
    wrong for two thirds of the collection.
    """
    n_folds = N_FOLDS if entry["source"].startswith("openml") else generated_folds
    applicable = sum(
        1
        for m in METHODS.values()
        if m.supports(entry["task"]) and m.implementation == "sklearn"
    )
    return applicable * n_folds * n_rates


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sample", type=int, help="run only the N smallest datasets")
    parser.add_argument("--rates", type=float, nargs="*", help="override missingness rates")
    args = parser.parse_args()

    logging.basicConfig(level=logging.ERROR, format="%(levelname)s %(message)s")
    config = load_config()
    seed_everything(config.run.seed)

    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    datasets = sorted(manifest["datasets"], key=lambda d: d["rows"])
    task_ids = manifest.get("openml_task_ids", {})
    if args.sample:
        datasets = datasets[: args.sample]

    rates = tuple(args.rates) if args.rates is not None else tuple(RATES)
    key = run_key(
        {
            "seed": config.run.seed,
            "n_folds": config.cv.n_folds,
            "rates": sorted(rates),
            "methods": sorted(METHODS),
        }
    )
    store = ResultStore(config.paths.datasets.parent / "results", key)
    completed = store.completed()

    total = sum(
        expected_evaluations(d, config.cv.n_folds, len(rates) + 1) for d in datasets
    )
    progress = Progress(total=total)

    report(f"{len(datasets)} datasets · missingness {(0.0, *rates)} · run {key}")
    report(f"~{total} evaluations expected, {len(completed)} already recorded\n")

    started = time.time()
    for index, entry in enumerate(datasets, start=1):
        features, target = load_frame(entry, config)
        folds = folds_for(entry, target, config, task_ids)
        original_rows = len(features)
        features, target, folds = cap_rows(features, target, folds, seed=config.run.seed)
        if len(features) < original_rows:
            report(f"  capped {original_rows:,} rows to {len(features):,} for evaluation")
        report(
            f"[{index}/{len(datasets)}] {entry['name']} "
            f"({len(features)} rows, {entry['task']}, {folds.n_folds} folds "
            f"from {folds.origin}) — {progress.line()}"
        )
        run_dataset(
            dataset=entry["name"],
            source=entry["source"],
            task=entry["task"],
            features=features,
            target=target,
            folds=folds,
            rates=rates,
            seed=config.run.seed,
            store=store,
            completed=completed,
            progress=progress,
            report=report,
        )

    store.flush()
    report(f"\nfinished in {(time.time() - started) / 60:.1f} minutes")
    report(f"{progress.done} evaluations · {progress.failures} did not score")
    report(f"results at {store.path.relative_to(PROJECT_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
