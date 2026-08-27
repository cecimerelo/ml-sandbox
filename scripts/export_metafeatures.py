"""Compute the meta-features for the collection and write them out.

The table Layer 2 trains on (#15), and evidence in its own right: it is what the thesis
points at when asked what the recommender actually reasons from.

    uv run python scripts/export_metafeatures.py
"""

from __future__ import annotations

import json
import warnings
from collections import Counter

from mlsandbox.config import PROJECT_ROOT, load_config
from mlsandbox.loading import load_any, split_target
from mlsandbox.metafeatures import MetaFeatures, from_dataset

warnings.filterwarnings("ignore")

MANIFEST = PROJECT_ROOT / "config" / "collection.json"
EXPORT_PATH = PROJECT_ROOT / "config" / "metafeatures.json"

FIELD_DOCS = {
    "task": "regression, binary or multiclass — three values, as FR-1.3 asks.",
    "rows": "Row band, not an exact count: the form cannot express more (D-027).",
    "features": "Predictor-count band.",
    "regime": (
        "Observations per predictor, as a stated mapping over the nine band combinations. "
        "Given explicitly because sixty training rows cannot be relied on to discover an "
        "interaction between two categorical variables."
    ),
    "feature_types": "numeric, categorical or mixed.",
    "missing": "none, some or a lot of missing predictor cells.",
    "class_balance": (
        "How far class proportions sit from equal. `not applicable` for regression rather "
        "than a default, which would mean nothing."
    ),
}


def compute(config) -> list[dict]:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    rows = []
    for entry in manifest["datasets"]:
        features, target = split_target(load_any(entry, config))
        meta: MetaFeatures = from_dataset(
            task=entry["task"], features=features, target=target.to_numpy()
        )
        rows.append({"dataset": entry["name"], "source": entry["source"], **meta.as_row()})
    return rows


def main() -> int:
    config = load_config()
    rows = compute(config)

    EXPORT_PATH.write_text(
        json.dumps({"_fields": FIELD_DOCS, "datasets": rows}, indent=2) + "\n",
        encoding="utf-8",
    )

    print(f"{len(rows)} datasets\n")
    for field in FIELD_DOCS:
        counts = Counter(row[field] for row in rows)
        print(f"  {field:15} {dict(counts)}")

    # An empty level is a case Layer 2 will meet in use and has never seen in training —
    # the same shape of gap as the sub-500-row band, and worth seeing here rather than
    # discovering from a confident wrong answer later.
    print(f"\nwritten to {EXPORT_PATH.relative_to(PROJECT_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
