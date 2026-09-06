"""Summaries of an uploaded dataset for the EDA block — never a row of it.

FR-7.2 promises the dataset is processed in memory and never stored; the EDA endpoints
promise something stronger for themselves. **An endpoint that cannot return a row cannot
leak one by accident.** Every function here reduces a column to bin edges, counts, or a
handful of summary numbers — nothing that lets an original value be read back out.

Two shapes for two kinds of column: a `Histogram` for anything numeric, `CategoricalBars`
for everything else, matching the same numeric/categorical test `metafeatures.from_dataset`
already uses (`pd.api.types.is_numeric_dtype`) — a column is read the same way whichever
path asks about it.
"""

from __future__ import annotations

from typing import Literal

import numpy as np
import pandas as pd

from mlsandbox.base import StrictModel

BIN_COUNT = 20
"""Fixed rather than data-dependent (Sturges, Freedman-Diaconis, ...): a histogram whose
bin count depends on the sample means two datasets of different sizes are not visually
comparable, and there is no reader-facing reason for this product to vary it."""

MAX_CATEGORIES_SHOWN = 15
"""DESIGN.md's categorical bar chart cap. Above this the tail folds into one `Other`
bar — never silently dropped, always named with the count it stands for."""


class HistogramBin(StrictModel):
    """One bar of a numeric histogram."""

    start: float
    end: float
    count: int


class Histogram(StrictModel):
    """A numeric column, reduced to bins. Never the values themselves."""

    column: str
    kind: Literal["numeric"] = "numeric"
    bins: list[HistogramBin]
    missing: int
    """Rows excluded because the value was blank, not folded into the first bin — a
    blank is not a low value, and silently placing it in one would misstate the shape."""


class CategoryCount(StrictModel):
    category: str
    count: int


class CategoricalBars(StrictModel):
    """A categorical column, reduced to its top categories plus a stated fold."""

    column: str
    kind: Literal["categorical"] = "categorical"
    categories: list[CategoryCount]
    """Frequency-descending, at most `MAX_CATEGORIES_SHOWN`."""

    other_count: int
    """Rows belonging to a category outside the top set. Zero when nothing was folded."""

    other_categories: int
    """How many distinct categories the fold represents — the `N` in `Other (N
    categories)`. Zero when nothing was folded."""

    missing: int


Distribution = Histogram | CategoricalBars


def summarise_column(values: pd.Series) -> Distribution:
    """Reduce one column to the shape its type calls for.

    The same test `metafeatures.from_dataset` uses to band `feature_types`
    (`pd.api.types.is_numeric_dtype`) decides the branch here, so a column is never
    numeric to one part of the system and categorical to another.
    """
    name = str(values.name)
    if pd.api.types.is_numeric_dtype(values):
        return _histogram(name, values)
    return _categorical_bars(name, values)


def _histogram(name: str, values: pd.Series) -> Histogram:
    present = values.dropna()
    missing = int(values.size - present.size)

    if present.empty:
        return Histogram(column=name, bins=[], missing=missing)

    lo, hi = float(present.min()), float(present.max())
    if lo == hi:
        # A constant column has no width to divide into bins; one bin holding
        # everything is the honest reading, not an arbitrary width around the value.
        return Histogram(
            column=name,
            bins=[HistogramBin(start=lo, end=hi, count=int(present.size))],
            missing=missing,
        )

    counts, edges = np.histogram(present.to_numpy(), bins=BIN_COUNT, range=(lo, hi))
    bins = [
        HistogramBin(start=float(edges[i]), end=float(edges[i + 1]), count=int(counts[i]))
        for i in range(len(counts))
    ]
    return Histogram(column=name, bins=bins, missing=missing)


def _categorical_bars(name: str, values: pd.Series) -> CategoricalBars:
    present = values.dropna()
    missing = int(values.size - present.size)

    counted = present.astype(str).value_counts()  # already frequency-descending
    shown = counted.iloc[:MAX_CATEGORIES_SHOWN]
    folded = counted.iloc[MAX_CATEGORIES_SHOWN:]

    return CategoricalBars(
        column=name,
        categories=[
            CategoryCount(category=str(category), count=int(count))
            for category, count in shown.items()
        ],
        other_count=int(folded.sum()),
        other_categories=int(folded.size),
        missing=missing,
    )


class ColumnKind(StrictModel):
    """A column's name and which chart form it gets — cheap to compute, so the feature
    picker can paginate without asking for every column's actual distribution."""

    column: str
    kind: Literal["numeric", "categorical"]


def column_kinds(frame: pd.DataFrame, *, target: str) -> list[ColumnKind]:
    """Every feature's kind, target excluded — the picker's inventory.

    Order matches the frame's own column order, which is the order the file was read in
    and therefore the order a reader already expects their columns in.
    """
    return [
        ColumnKind(
            column=str(column),
            kind="numeric" if pd.api.types.is_numeric_dtype(frame[column]) else "categorical",
        )
        for column in frame.columns
        if column != target
    ]
