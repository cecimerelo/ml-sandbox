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

    licence: str | None = None
    """Terms the dataset is published under, where the source states them.

    The reason OpenML became the primary source (D-025): PMLB leaves this unfilled for
    most of its collection, and a licence nobody can read cannot be complied with.
    `None` means unreported, which is not the same as unrestricted.
    """

    origin: str | None = None
    """Where the dataset came from, as a URL. What lets a reader follow the evidence back
    past this study."""
    """How far the class proportions sit from equal: 0 is a perfect split, and PMLB's
    most skewed binary dataset reaches 0.94.

    **Only meaningful for classification.** PMLB populates it for regression too — 59 of
    its 271 regression datasets carry a non-zero value — where it describes nothing.
    Read it through `class_imbalance`, which returns None off the classification path.
    """

    @property
    def is_classification(self) -> bool:
        return self.task == "classification"

    @property
    def class_imbalance(self) -> float | None:
        """Class imbalance, or None when the question does not apply.

        The third field where PMLB reports a value that only means something for
        classification — after `classes` and, through it, the multiclass count. Both
        earlier cases became bugs that produced plausible wrong numbers, so this one is
        guarded at the source rather than at each call site.
        """
        return self.imbalance if self.is_classification else None
