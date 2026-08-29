"""Report the research metrics: the thesis's answer, as a table.

    uv run python scripts/report_metrics.py

Reads whatever the benchmark has recorded so far, so it is safe to run mid-run — the
dataset count in the output says how much of the collection it speaks for. Partial numbers
are not a random sample of the collection, since the benchmark works through it in order.
"""

from __future__ import annotations

import argparse
import json
import warnings

import pandas as pd

from mlsandbox.config import PROJECT_ROOT, load_config
from mlsandbox.evaluation import TOP_K, cost_of_explainability, evaluate
from mlsandbox.methods import METHODS
from mlsandbox.missingness import RATES
from mlsandbox.results import store_for

warnings.filterwarnings("ignore")

METAFEATURES = PROJECT_ROOT / "config" / "metafeatures.json"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--missing-rate", type=float, default=0.0)
    args = parser.parse_args()

    config = load_config()
    # Shared with the benchmark so both agree on which file this run's results live in.
    results = store_for(config, rates=RATES, methods=METHODS).load()
    if results.empty:
        raise SystemExit("No results yet. Run scripts/run_benchmark.py first.")

    metafeatures = pd.DataFrame(json.loads(METAFEATURES.read_text())["datasets"])
    metafeatures = metafeatures[metafeatures.dataset.isin(results.dataset.unique())]

    print(f"\n{results.dataset.nunique()} datasets, missingness {args.missing_rate:.0%}")

    # Both strata, always. The pooled figure alone understates every strategy's margin,
    # because most datasets have several methods tied for best and hand a hit to all of
    # them; the narrowed figure alone would look like a subset chosen to flatter.
    for narrowed, heading in (
        (False, "every dataset"),
        (True, "only where the choice makes a difference"),
    ):
        scores = evaluate(
            results,
            metafeatures,
            seed=config.run.seed,
            missing_rate=args.missing_rate,
            only_discriminating=narrowed,
        )
        scores.sort(key=lambda s: -s.hit_rate)
        counted = scores[0].datasets if scores else 0
        print(f"\n  {heading} ({counted} datasets)\n")
        print(f"  {'strategy':22} {'hit':>6} {f'top-{TOP_K}':>7} {'regret':>8}")
        print("  " + "-" * 46)
        for score in scores:
            print(
                f"  {score.strategy:22} {score.hit_rate:6.2f} "
                f"{score.top_k_hit_rate:7.2f} {score.mean_regret:8.3f}"
            )

    print("\nWhat requiring explainability costs:\n")
    for level in ("somewhat", "critical"):
        cost = cost_of_explainability(
            results,
            metafeatures,
            seed=config.run.seed,
            level=level,
            missing_rate=args.missing_rate,
        )
        # Where the constraint never binds, the cost is zero by construction rather than by
        # evidence — saying so stops a reassuring zero from being read as a finding.
        bound = cost.datasets_where_it_bound
        note = "" if bound else "  (never binding: no cost to measure)"
        print(f"  {level:10} {cost.cost:+8.3f} regret   binds on {bound} datasets{note}")
    print()


if __name__ == "__main__":
    main()
