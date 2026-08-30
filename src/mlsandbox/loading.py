"""Loading a dataset, whatever source it came from.

The collection is mixed (D-025), so dispatching on source is not a nicety: calling PMLB's
loader for an OpenML dataset fails on every one of them.

Lives here rather than in the script that first needed it. A function defined in a script
is a function nobody else can import — a lesson this project has now learned twice.
"""

from __future__ import annotations

import pandas as pd

from mlsandbox.config import Config
from mlsandbox.pmlb_source import load_dataset as load_pmlb

TARGET_COLUMN = "target"
"""What the outcome column is called by the time anything downstream sees it. PMLB's
convention, adopted for both sources so nothing has to branch on where a dataset came
from."""


def load_any(entry: dict, config: Config) -> pd.DataFrame:
    """Load the dataset described by one manifest entry, from disk."""
    if entry["source"] == "pmlb":
        return load_pmlb(entry["name"], config)

    import openml

    from mlsandbox.openml_source import configure as configure_openml

    configure_openml(config)
    dataset_id = int(entry["origin"].rsplit("/", 1)[1])
    record = openml.datasets.get_dataset(dataset_id, download_data=True)
    frame, _, _, _ = record.get_data(dataset_format="dataframe")

    # OpenML declares which column is the outcome, and it is not reliably the last one:
    # five of the forty datasets here put it elsewhere. Renamed to PMLB's convention so
    # both sources answer the same question the same way, and so the guess below is never
    # reached for a source that knows the answer.
    declared = record.default_target_attribute
    if not declared or declared not in frame.columns:
        raise ValueError(
            f"{entry['name']}: OpenML declares target {declared!r}, which is not a column. "
            "Guessing here is how the study ends up predicting the wrong thing."
        )
    if TARGET_COLUMN in frame.columns and declared != TARGET_COLUMN:
        raise ValueError(
            f"{entry['name']}: has a predictor named {TARGET_COLUMN!r} but declares "
            f"{declared!r} as the outcome. Renaming would lose one of them."
        )
    return frame.rename(columns={declared: TARGET_COLUMN})


def split_target(frame: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series]:
    """Separate predictors from the outcome.

    Both sources name it `target` by the time a frame reaches here — PMLB natively, OpenML
    via the rename in `load_any`. Resolved in one place so the benchmark and the
    meta-features cannot disagree about which column is being predicted.

    **There is no fallback, deliberately.** This used to take the last column when the name
    was absent, on the belief that OpenML puts the outcome last. It does not: five of the
    forty OpenML datasets declare a target elsewhere, so `kings_county` was trained to
    predict the day of the month from the house's price and features. That produced R² of
    0.00 to 0.04 for every method — numbers that look like a finding about a hard dataset
    rather than like a bug. A guess that is usually right is worse here than an error,
    because nothing downstream can tell the difference.
    """
    if TARGET_COLUMN not in frame.columns:
        raise ValueError(
            f"No {TARGET_COLUMN!r} column. The loader is responsible for naming the "
            "outcome; guessing at this point is what this function exists not to do."
        )
    return frame.drop(columns=[TARGET_COLUMN]), frame[TARGET_COLUMN]
