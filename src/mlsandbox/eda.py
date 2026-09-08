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

MAX_CORRELATION_FEATURES = 30
"""NFR-2 permits 500 features, which is 250,000 cells at 500×500 — the chart does not
attempt it. Top-K by variance, K capped here, is DESIGN.md's stated guard."""

IN_CELL_NUMBERS_MAX = 20
"""Above this the correlation matrix drops its in-cell `r` values — an 11px number does
not fit a cell smaller than the panel forces it to be past this point."""

OUTLIER_IQR_MULTIPLE = 1.5
"""Tukey's fence — the conventional boxplot definition, not a choice specific to this
product."""


class HistogramBin(StrictModel):
    """One bar of a numeric histogram."""

    start: float
    end: float
    count: int


class BoxplotSummary(StrictModel):
    """The five-number summary, plus the points Tukey's fence calls outliers.

    `outliers` are individual values, not rows — the same class of disclosure as a
    histogram's bin edges (already single-column extremes), never tied to any other
    column's value in the same row.
    """

    minimum: float
    """The lowest **inlier** — the lower whisker's actual end, not the fence formula's
    raw endpoint, which can fall outside the data entirely."""
    q1: float
    median: float
    q3: float
    maximum: float
    """The highest inlier, symmetric with `minimum`."""
    outliers: list[float]


class Histogram(StrictModel):
    """A numeric column, reduced to bins. Never the values themselves."""

    column: str
    kind: Literal["numeric"] = "numeric"
    bins: list[HistogramBin]
    missing: int
    """Rows excluded because the value was blank, not folded into the first bin — a
    blank is not a low value, and silently placing it in one would misstate the shape."""

    boxplot: BoxplotSummary | None
    """`None` only when every value is missing — there is nothing to summarise."""


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
        return Histogram(column=name, bins=[], missing=missing, boxplot=None)

    # `is_numeric_dtype` counts booleans as numeric — correctly, a `has_garden` column
    # is a 0/1 measurement here, not a category — but numpy's own quantile machinery
    # cannot subtract two bools to interpolate between them. Every numeric subtype
    # becomes plain float before any arithmetic runs, which is also harmless for the
    # int/float columns that already were one.
    present = present.astype(float)

    boxplot = _boxplot(present)

    lo, hi = float(present.min()), float(present.max())
    if lo == hi:
        # A constant column has no width to divide into bins; one bin holding
        # everything is the honest reading, not an arbitrary width around the value.
        return Histogram(
            column=name,
            bins=[HistogramBin(start=lo, end=hi, count=int(present.size))],
            missing=missing,
            boxplot=boxplot,
        )

    counts, edges = np.histogram(present.to_numpy(), bins=BIN_COUNT, range=(lo, hi))
    bins = [
        HistogramBin(start=float(edges[i]), end=float(edges[i + 1]), count=int(counts[i]))
        for i in range(len(counts))
    ]
    return Histogram(column=name, bins=bins, missing=missing, boxplot=boxplot)


def _boxplot(present: pd.Series) -> BoxplotSummary:
    q1, median, q3 = (float(v) for v in present.quantile([0.25, 0.5, 0.75]))
    iqr = q3 - q1
    lower_fence = q1 - OUTLIER_IQR_MULTIPLE * iqr
    upper_fence = q3 + OUTLIER_IQR_MULTIPLE * iqr

    inliers = present[(present >= lower_fence) & (present <= upper_fence)]
    outliers = present[(present < lower_fence) | (present > upper_fence)]

    # A constant column (iqr == 0) makes every fence equal to q1/q3, so nothing is
    # outside it and `inliers` is never empty here — but if it somehow were, min/max
    # is the honest fallback rather than a fence that may not correspond to any value.
    minimum = float(inliers.min()) if not inliers.empty else float(present.min())
    maximum = float(inliers.max()) if not inliers.empty else float(present.max())

    return BoxplotSummary(
        minimum=minimum,
        q1=q1,
        median=median,
        q3=q3,
        maximum=maximum,
        outliers=[float(v) for v in outliers],
    )


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


class CorrelationMatrix(StrictModel):
    """Pairwise Pearson correlation among the highest-variance numeric features.

    `values[i][j]` is the correlation between `features[i]` and `features[j]`, in the
    same order both ways — a real matrix, not a flattened cell list, because that is
    what a reader (and a heatmap) actually wants to index by.
    """

    features: list[str]
    """At most `MAX_CORRELATION_FEATURES`, by variance descending."""

    values: list[list[float]]

    total_numeric: int
    """How many numeric features existed before the cap — what the truncation caption
    states against (`"...of 500"`)."""


def correlation_matrix(frame: pd.DataFrame, *, exclude: str) -> CorrelationMatrix:
    """The correlation heatmap's data, target excluded.

    Fewer than two numeric features (including the all-categorical case) returns an
    empty matrix rather than raising — there is nothing to correlate, and that is a
    state for the panel to render, not an error.
    """
    numeric = frame.drop(columns=[exclude], errors="ignore").select_dtypes(include="number")
    total_numeric = len(numeric.columns)

    if total_numeric < 2:
        return CorrelationMatrix(features=[], values=[], total_numeric=total_numeric)

    top = numeric.var(numeric_only=True).sort_values(ascending=False)
    features = [str(c) for c in top.index[:MAX_CORRELATION_FEATURES]]

    # A constant column has no correlation with anything, and pandas says so with NaN —
    # not valid JSON, and not a value a heatmap cell can render. Read as zero: a constant
    # column carries no signal to correlate, which is what zero already means here.
    correlations = numeric[features].corr().fillna(0.0)
    values = [[float(v) for v in row] for row in correlations.to_numpy()]

    return CorrelationMatrix(features=features, values=values, total_numeric=total_numeric)
