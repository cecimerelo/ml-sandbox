"""The study's dataset vocabulary, independent of where a dataset came from.

Sources disagree on details — OpenML counts the target column among its features, PMLB
does not; PMLB reports no missing-value count because its datasets are pre-cleaned. Every
source normalises into this type so the selection rules never branch on provenance.
"""

from __future__ import annotations

from mlsandbox.base import StrictModel


class Dataset(StrictModel):
    name: str
    source: str
    """Which collection this came from, e.g. `pmlb`. Recorded because a mixed collection
    has to be able to explain itself."""

    revision: str
    """The exact version fetched — a commit SHA for PMLB. This is what makes the study
    re-runnable against identical bytes rather than "whatever is there now"."""

    rows: int
    predictors: int
    """Excludes the target column, whatever the source's own convention."""

    task: str
    """`classification` or `regression`, as the source reports it.

    Carried explicitly rather than inferred from `classes`: PMLB does not zero out
    `n_classes` for regression datasets, so deriving the task from it silently classes
    every regression dataset as classification.
    """

    classes: int

    categorical_predictors: int
    missing_values: int | None = None
    """`None` means the source does not report it — which is not the same as zero, and
    the difference matters when claiming coverage of the missing-value case."""

    imbalance: float | None = None

    @property
    def is_classification(self) -> bool:
        return self.task == "classification"
