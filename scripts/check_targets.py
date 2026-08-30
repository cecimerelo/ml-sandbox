"""Verify that every dataset predicts what it is supposed to predict.

    uv run python scripts/check_targets.py

Not a unit test: it loads the whole collection, which needs the data and several minutes.
It exists because the failure it checks for is silent — a wrongly chosen target does not
raise, it produces scores that read as a difficult dataset.

Run it after changing anything about loading, and before trusting a set of results.
"""

from __future__ import annotations

import json
import warnings

import pandas as pd

from mlsandbox.config import PROJECT_ROOT, load_config
from mlsandbox.loading import load_any, split_target

warnings.filterwarnings("ignore")

MANIFEST = PROJECT_ROOT / "config" / "collection.json"


def main() -> int:
    config = load_config()
    entries = json.loads(MANIFEST.read_text())["datasets"]

    problems: list[str] = []
    for entry in entries:
        name = entry["name"]
        try:
            features, target = split_target(load_any(entry, config))
        except Exception as error:  # noqa: BLE001 — reporting, not handling
            problems.append(f"{name}: could not load — {error}")
            continue

        # A regression target that arrives as labels is the shape of the target bug: the
        # column chosen was a category, so it was not the outcome.
        if entry["task"] == "regression" and not pd.api.types.is_numeric_dtype(target):
            problems.append(f"{name}: regression target is {target.dtype}, not a number")

        if target.nunique() <= 1:
            problems.append(f"{name}: target has one value — nothing to predict")

        if entry["task"] == "regression" and target.nunique() < 10:
            # Not necessarily wrong, but a continuous outcome with a handful of values is
            # usually a category that was picked by mistake.
            problems.append(
                f"{name}: regression target takes only {target.nunique()} values — check it"
            )

        if features.shape[1] == 0:
            problems.append(f"{name}: no predictors left after removing the target")

    print(f"{len(entries)} datasets checked")
    for problem in problems:
        print(f"  {problem}")
    print("\nall targets look right" if not problems else f"\n{len(problems)} to look at")
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
