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
    return frame


def split_target(frame: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series]:
    """Separate predictors from the outcome.

    PMLB names every outcome `target`; OpenML puts it last. Resolved in one place so the
    benchmark and the meta-features cannot disagree about which column is being predicted.
    """
    target_column = "target" if "target" in frame.columns else frame.columns[-1]
    return frame.drop(columns=[target_column]), frame[target_column]
