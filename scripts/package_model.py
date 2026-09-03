"""Package Layer 2 for the application.

    uv run python scripts/package_model.py

Reads whatever the benchmark has recorded and writes a loadable artifact beside it. Safe to
run mid-run: the card says how many datasets the model saw, and the application reports it.
A model trained on part of the collection is useful for building against and must never be
mistaken for the finished one.
"""

from __future__ import annotations

import json
import warnings

import pandas as pd

from mlsandbox import artifact
from mlsandbox.config import PROJECT_ROOT, load_config
from mlsandbox.methods import METHODS
from mlsandbox.missingness import RATES
from mlsandbox.results import store_for

warnings.filterwarnings("ignore")

METAFEATURES = PROJECT_ROOT / "config" / "metafeatures.json"
COLLECTION = PROJECT_ROOT / "config" / "collection.json"


def main() -> int:
    config = load_config()
    results = store_for(config, rates=RATES, methods=METHODS).load()
    if results.empty:
        raise SystemExit("No results yet. Run scripts/run_benchmark.py first.")

    metafeatures = pd.DataFrame(json.loads(METAFEATURES.read_text())["datasets"])
    collection = json.loads(COLLECTION.read_text())["datasets"]

    built = artifact.build(
        results,
        metafeatures[metafeatures.dataset.isin(results.dataset.unique())],
        seed=config.run.seed,
        collection_size=len(collection),
        known_datasets={d["name"] for d in collection},
    )

    path = config.paths.datasets.parent / "model" / "layer2.joblib"
    artifact.save(built, path)

    print(built.card.summary())
    print(f"\nwritten to {path.relative_to(PROJECT_ROOT)}")

    # The thinnest evidence in the collection, so a reader knows which answers the model
    # is barely qualified to speak about before it speaks about them.
    thin = sorted(
        (
            (count, field, answer)
            for field, answers in built.card.answer_support.items()
            for answer, count in answers.items()
        )
    )[:3]
    print("\nleast-supported answers:")
    for count, field, answer in thin:
        print(f"  {field} = {answer!r}: {count} of {built.card.datasets} datasets")
    if built.card.is_provisional:
        print(
            "\nPROVISIONAL — the benchmark has not finished. Fine to build against, "
            "and regenerate before anything is reported from it."
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
