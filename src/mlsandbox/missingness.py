"""Controlled injection of missing values.

PMLB's datasets are pre-cleaned and carry no missing values, so the recommender's
missing-value heuristic — prefer trees and ensembles when data has gaps, since linear
methods need imputation first — would go unvalidated (D-015).

Injecting gaps at known rates turns that into a controlled experiment: domain, noise,
features and sample size stay fixed, and only the missing-value rate moves. Whatever
change in the winning method that produces is attributable to missingness alone.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

TARGET_COLUMN = "target"
"""PMLB names every outcome column `target`, which is what lets the study treat its
datasets uniformly."""

RATES = (0.05, 0.25)
"""Injected fractions of predictor cells, chosen to land either side of FR-1.3's bands:
5% reads as "some", 25% as "a lot". Two rates rather than a sweep, because D-011's
schedule buys coverage of the dimension, not a study of it."""


def inject_missing(
    frame: pd.DataFrame,
    *,
    rate: float,
    seed: int,
    target_column: str = TARGET_COLUMN,
) -> pd.DataFrame:
    """Return a copy with `rate` of its predictor cells set to NaN, completely at random.

    **The target is never touched.** Removing outcomes would change what is being
    predicted rather than how hard it is to predict, and would quietly shrink the
    effective sample instead of testing missingness.

    Missingness is MCAR — every predictor cell is equally likely to go. That is the
    weakest and most neutral assumption; real gaps are often MAR or MNAR, where the
    pattern itself carries signal. Stated plainly, MCAR is a floor: methods that cannot
    cope here will not cope with the harder kinds either.
    """
    if not 0 <= rate < 1:
        raise ValueError(f"rate must be in [0, 1), got {rate}")

    result = frame.copy()
    predictors = [column for column in result.columns if column != target_column]
    if not predictors or rate == 0:
        return result

    rng = np.random.default_rng(seed)
    total_cells = len(result) * len(predictors)
    to_blank = int(round(total_cells * rate))
    if to_blank == 0:
        return result

    # Choose flat positions without replacement so the achieved rate matches the
    # requested one exactly, rather than approximately as independent draws would.
    flat_positions = rng.choice(total_cells, size=to_blank, replace=False)
    row_indices, column_indices = np.divmod(flat_positions, len(predictors))

    # Columns must hold NaN, which integer dtypes cannot; float is the narrowest type
    # that can, and converting up front avoids a per-assignment dtype warning.
    for column in predictors:
        if pd.api.types.is_integer_dtype(result[column]):
            result[column] = result[column].astype("float64")

    for row_index, column_index in zip(row_indices, column_indices, strict=True):
        result.iat[row_index, result.columns.get_loc(predictors[column_index])] = np.nan

    return result


def missing_rate(frame: pd.DataFrame, *, target_column: str = TARGET_COLUMN) -> float:
    """Fraction of predictor cells that are missing. The inverse of `inject_missing`."""
    predictors = [column for column in frame.columns if column != target_column]
    if not predictors or frame.empty:
        return 0.0
    return float(frame[predictors].isna().to_numpy().sum()) / (len(frame) * len(predictors))
