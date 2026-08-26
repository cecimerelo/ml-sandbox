"""Fold assignments: generated once, then read by every method.

The contract is not about who authors the splits — it is that there is exactly one source
of truth for them (D-003). Two methods scored on different partitions of the same dataset
cannot be compared, and nothing about that failure announces itself: the numbers simply
mean less than they appear to.

OpenML's suites ship their own splits and those are used, which is what makes results
contrastable with published work on CC18. PMLB ships none, so its folds are generated
here under the same contract.
"""

from __future__ import annotations

import numpy as np
from sklearn.model_selection import KFold, StratifiedKFold

from mlsandbox.base import StrictModel

Fold = tuple[list[int], list[int]]
"""One (train, test) pair of row indices."""


class FoldSet(StrictModel):
    """The partitions for one dataset, and where they came from.

    `origin` is recorded because the collection mixes sources: an OpenML dataset uses the
    suite's published folds while a PMLB one uses generated ones, and a reader comparing
    two datasets deserves to know which is which.
    """

    dataset: str
    origin: str
    """`openml` for a suite's published splits, `generated` for ours."""

    folds: list[Fold]

    @property
    def n_folds(self) -> int:
        return len(self.folds)

    def covers(self, n_rows: int) -> bool:
        """Whether every row appears exactly once as a test case across the folds.

        The property that makes cross-validation cross-validation. A partition that misses
        rows silently evaluates on less data than the dataset contains.
        """
        seen = [index for _, test in self.folds for index in test]
        return sorted(seen) == list(range(n_rows))


def generate(
    dataset: str,
    *,
    target: np.ndarray,
    n_folds: int,
    seed: int,
    stratified: bool,
) -> FoldSet:
    """Build folds for a dataset that ships none.

    Stratified for classification so every fold keeps the class proportions — without it,
    a rare class can be absent from a training fold entirely, and the method is then
    blamed for a split it never had a chance at.
    """
    splitter = (
        StratifiedKFold(n_splits=n_folds, shuffle=True, random_state=seed)
        if stratified
        else KFold(n_splits=n_folds, shuffle=True, random_state=seed)
    )
    indices = np.arange(len(target))
    folds = [
        (train.tolist(), test.tolist())
        for train, test in splitter.split(indices, target if stratified else None)
    ]
    return FoldSet(dataset=dataset, origin="generated", folds=folds)


def from_openml(dataset: str, folds: list[Fold]) -> FoldSet:
    return FoldSet(dataset=dataset, origin="openml", folds=folds)
