"""Measure how long the benchmark will actually take.

Every estimate about compute so far has been guesswork. This runs a representative slice
— a few datasets across the size bands, a few methods across the cost spectrum — and
reports seconds per cross-validated fit, so the method count in #9 is chosen from
measurement rather than intuition.

    uv run python scripts/pilot_timing.py
"""

from __future__ import annotations

import json
import time
import warnings

from sklearn.ensemble import (
    GradientBoostingClassifier,
    GradientBoostingRegressor,
    RandomForestClassifier,
    RandomForestRegressor,
)
from sklearn.linear_model import LinearRegression, LogisticRegression, Ridge
from sklearn.model_selection import KFold, StratifiedKFold, cross_val_score
from sklearn.neighbors import KNeighborsClassifier, KNeighborsRegressor
from sklearn.neural_network import MLPClassifier, MLPRegressor
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC, SVR
from sklearn.tree import DecisionTreeClassifier, DecisionTreeRegressor

from mlsandbox.config import PROJECT_ROOT, load_config
from mlsandbox.pmlb_source import load_dataset

warnings.filterwarnings("ignore")

# (classification estimator, regression estimator, needs feature scaling)
METHODS = {
    "linear": (LogisticRegression, LinearRegression, True),
    "ridge": (lambda **kw: LogisticRegression(penalty="l2", **kw), Ridge, True),
    "knn": (KNeighborsClassifier, KNeighborsRegressor, True),
    "tree": (DecisionTreeClassifier, DecisionTreeRegressor, False),
    "random_forest": (RandomForestClassifier, RandomForestRegressor, False),
    "boosting": (GradientBoostingClassifier, GradientBoostingRegressor, False),
    "svm": (SVC, SVR, True),
    "mlp": (MLPClassifier, MLPRegressor, True),
}

TIMEOUT_MARKER = -1.0
"""Recorded when a method blows past the tier's budget. A timeout is data, not a gap."""


def pick_datasets(manifest: dict, per_band: int = 2) -> list[dict]:
    """Two datasets per size band per task, spanning the real range."""
    chosen: list[dict] = []
    for task in ("classification", "regression"):
        for low, high in ((0, 500), (500, 10_000), (10_000, 10**9)):
            band = sorted(
                (d for d in manifest["datasets"] if d["task"] == task and low <= d["rows"] < high),
                key=lambda d: d["rows"],
            )
            if band:
                chosen.append(band[0])
                if len(band) > 1 and per_band > 1:
                    chosen.append(band[-1])
    return chosen


def time_one(dataset: dict, method: str, config, budget_seconds: float) -> float:
    frame = load_dataset(dataset["name"], config)
    target = frame["target"].to_numpy()
    features = frame.drop(columns=["target"]).to_numpy()

    classification, regression, needs_scaling = METHODS[method]
    is_classification = dataset["task"] == "classification"
    estimator = classification() if is_classification else regression()
    if needs_scaling:
        estimator = make_pipeline(StandardScaler(), estimator)

    folds = (
        StratifiedKFold(n_splits=5, shuffle=True, random_state=config.run.seed)
        if is_classification
        else KFold(n_splits=5, shuffle=True, random_state=config.run.seed)
    )

    started = time.perf_counter()
    try:
        cross_val_score(estimator, features, target, cv=folds, n_jobs=1)
    except Exception:
        return TIMEOUT_MARKER
    elapsed = time.perf_counter() - started
    return elapsed if elapsed <= budget_seconds else TIMEOUT_MARKER


def main() -> int:
    config = load_config()
    manifest = json.loads((PROJECT_ROOT / "config" / "collection.json").read_text())
    datasets = pick_datasets(manifest)

    header = f"{'dataset':30} {'rows':>7} {'task':14} " + " ".join(f"{m[:9]:>9}" for m in METHODS)
    print(header, flush=True)
    print("-" * len(header), flush=True)

    totals: dict[str, list[float]] = {m: [] for m in METHODS}
    for dataset in datasets:
        budget = 60.0 if dataset["rows"] < 500 else 120.0 if dataset["rows"] <= 10_000 else 300.0
        row = []
        print(f"  ... {dataset['name'][:40]} ({dataset['rows']} rows)", flush=True)
        for method in METHODS:
            seconds = time_one(dataset, method, config, budget)
            totals[method].append(seconds)
            row.append("  timeout" if seconds == TIMEOUT_MARKER else f"{seconds:9.1f}")
        print(
            f"{dataset['name'][:30]:30} {dataset['rows']:>7} "
            f"{dataset['task']:14} " + " ".join(row),
            flush=True,
        )

    print("\nseconds per 5-fold cross-validation, summed over the sampled datasets")
    grand_total = 0.0
    for method, times in totals.items():
        completed = [t for t in times if t != TIMEOUT_MARKER]
        timeouts = len(times) - len(completed)
        total = sum(completed)
        grand_total += total
        note = f"  ({timeouts} timed out)" if timeouts else ""
        print(f"  {method:16} {total:8.1f}s over {len(completed)} datasets{note}")

    sampled = len(datasets)
    all_datasets = len(manifest["datasets"])
    print(f"\nmeasured {sampled} of {all_datasets} datasets, {len(METHODS)} methods")
    if sampled:
        scaled = grand_total / sampled * all_datasets
        print(f"naive extrapolation to the full collection: {scaled / 60:.0f} min")
        print(f"  x3 missingness variants: {scaled * 3 / 60:.0f} min")
        print(f"  across 12 cores:         {scaled * 3 / 60 / 12:.0f} min")
        print(
            "\nThe extrapolation is optimistic: the sample is drawn from the extremes of "
            "each band,\nbut timed-out methods contribute nothing to the total while "
            "still costing their budget."
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
