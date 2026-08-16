"""Shared fixtures.

Nothing here touches the network. A suite that needs GitHub to be reachable fails for
reasons unrelated to the code, which is the exact problem that pushed the study off
OpenML.
"""

import pytest

from mlsandbox.config import Config

SUMMARY_HEADER = (
    "dataset\tn_instances\tn_features\tn_classes\ttask"
    "\tn_categorical_features\timbalance"
)


@pytest.fixture
def config(tmp_path) -> Config:
    return Config.model_validate(
        {
            "run": {"seed": 1},
            "cv": {"n_folds": 5},
            "paths": {"datasets": str(tmp_path)},
        }
    )
