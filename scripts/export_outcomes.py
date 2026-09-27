"""Compute what every strategy chose on every held-out dataset, and write it out.

    uv run python scripts/export_outcomes.py

The input the Colab notebook draws its charts from. Leave-one-dataset-out over 106 datasets
takes minutes per missingness rate, which is too long to ask of a reader opening the
notebook, so it is computed once here and committed next to the results it came from. The
notebook can still recompute it, and says how.

Writes `data/results/outcomes.parquet` (one row per missingness rate, dataset and strategy),
`data/results/method_scores.parquet` (every method's mean score per dataset, and whether the
tie rule counts it among the best) and `data/results/explainability.json` (the cost of each
explainability level, at 0%).
"""

from __future__ import annotations

import json
import warnings

import pandas as pd

from mlsandbox.baselines import summarise
from mlsandbox.config import PROJECT_ROOT, load_config
from mlsandbox.evaluation import cost_of_explainability, outcomes
from mlsandbox.methods import METHODS
from mlsandbox.missingness import RATES
from mlsandbox.results import store_for

warnings.filterwarnings("ignore")

METAFEATURES = PROJECT_ROOT / "config" / "metafeatures.json"
OUTCOMES_PATH = PROJECT_ROOT / "data" / "results" / "outcomes.parquet"
EXPLAINABILITY_PATH = PROJECT_ROOT / "data" / "results" / "explainability.json"
METHOD_SCORES_PATH = PROJECT_ROOT / "data" / "results" / "method_scores.parquet"


def method_scores(results: pd.DataFrame) -> pd.DataFrame:
    """Every method's mean score on every dataset, with the tie rule already applied.

    Exported rather than recomputed in the notebook, so the charts that ask *"which method
    wins?"* use the same one-standard-deviation rule as every other figure in the study.
    """
    rows = [
        {
            "missing_rate": rate,
            "dataset": summary.dataset,
            "method": method,
            "score": score,
            "regret": summary.best_score - score,
            "winner": summary.is_hit(method),
        }
        for rate in sorted(results.missing_rate.unique())
        for summary in summarise(results, missing_rate=rate)
        for method, score in summary.scores.items()
    ]
    return pd.DataFrame(rows)


def main() -> None:
    config = load_config()
    store = store_for(config, rates=RATES, methods=METHODS)
    results = store.load()
    if results.empty:
        raise SystemExit("No results yet. Run scripts/run_benchmark.py first.")
    metafeatures = pd.DataFrame(json.loads(METAFEATURES.read_text())["datasets"])
    metafeatures = metafeatures[metafeatures.dataset.isin(results.dataset.unique())]

    method_scores(results).to_parquet(METHOD_SCORES_PATH, index=False)

    frames = []
    for rate in (0.0, *RATES):
        print(f"outcomes at {rate:.0%} missingness…", flush=True)
        frame = outcomes(results, metafeatures, seed=config.run.seed, missing_rate=rate)
        frames.append(frame.assign(missing_rate=rate))
    pd.concat(frames, ignore_index=True).to_parquet(OUTCOMES_PATH, index=False)

    costs = []
    for level in ("somewhat", "critical"):
        print(f"cost of explainability, {level}…", flush=True)
        cost = cost_of_explainability(results, metafeatures, seed=config.run.seed, level=level)
        costs.append({**cost.model_dump(), "cost": cost.cost})
    EXPLAINABILITY_PATH.write_text(
        json.dumps({"results": store.path.name, "levels": costs}, indent=2) + "\n"
    )
    print(f"wrote {OUTCOMES_PATH.name}, {METHOD_SCORES_PATH.name}, {EXPLAINABILITY_PATH.name}")


if __name__ == "__main__":
    main()
