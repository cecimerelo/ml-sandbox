"""Selection rules for the benchmark collection.

Every dataset that enters the study, and every one that does not, passes through here.
Exclusions carry a reason rather than being filtered away silently: a collection whose
gaps cannot be explained invites the suspicion that datasets were picked to flatter the
heuristics.

The rules are expressed against the product's own scope (NFR-2, FR-1.3) so the selection
is justified by constraints already written down rather than invented for this study
(D-004).
"""

from __future__ import annotations

import re

from mlsandbox.base import StrictModel
from mlsandbox.openml_client import DatasetMetadata

MAX_FEATURES = 500
"""NFR-2. Also removes the image-derived datasets in CC18, whose pixel columns run to 785
and beyond (D-004)."""

SMALL_BAND_MAX_ROWS = 500
"""FR-1.3's lowest band. Neither curated suite contains anything below this, which is why
D-006 subsamples and D-007 pins real small datasets."""

IMAGE_DERIVED = frozenset({"mnist_784", "Fashion-MNIST", "Devnagari-Script", "CIFAR_10"})
"""Datasets whose columns are flattened pixels. The feature cap already removes these;
naming them makes the intent explicit rather than incidental, and catches any that would
otherwise slip under the cap."""


class Excluded(StrictModel):
    dataset_id: int
    name: str
    reason: str


class Screening(StrictModel):
    kept: list[DatasetMetadata]
    excluded: list[Excluded]

    @property
    def total(self) -> int:
        return len(self.kept) + len(self.excluded)


def screen_one(meta: DatasetMetadata, *, require_small: bool = False) -> str | None:
    """Return why this dataset is excluded, or None if it is kept.

    `require_small` applies to the pinned candidates of D-007, which earn their place only
    by covering the sub-500-row band the curated suites lack. A dataset above that
    threshold is not rejected for being poor — it is simply already covered.
    """
    if meta.name in IMAGE_DERIVED:
        return "image-derived: out of scope per NFR-2"
    if meta.features > MAX_FEATURES:
        return f"{meta.features} features exceeds the {MAX_FEATURES} cap (NFR-2)"
    if meta.rows == 0:
        return "no reported row count: metadata incomplete"
    if require_small and meta.rows >= SMALL_BAND_MAX_ROWS:
        return (
            f"{meta.rows} rows is at or above {SMALL_BAND_MAX_ROWS}: "
            "already covered by the curated suites"
        )
    return None


def family_of(name: str) -> str:
    """Best-effort family key for a dataset name.

    OpenML carries whole families that are one source described several ways —
    `one-hundred-plants-margin` / `-shape` / `-texture`, or the `analcatdata_*` and `fri_c*`
    collections. Admitting many members would make a band look varied while being a single
    kind of data (D-007).

    This is a heuristic meant to *flag* candidates for human review, not to decide alone.
    """
    parts = [p for p in re.split(r"[_\-.]", name.lower()) if p]
    if len(parts) <= 1:
        return name.lower()
    if len(parts) > 2:
        return "-".join(parts[:-1])
    return parts[0]


def screen(
    candidates: list[DatasetMetadata],
    *,
    require_small: bool = False,
    max_per_family: int = 1,
) -> Screening:
    """Apply the selection rules in a stable order.

    Family de-duplication runs after the per-dataset rules, so a family is never
    represented by a member that would have been excluded on its own merits.
    """
    kept: list[DatasetMetadata] = []
    excluded: list[Excluded] = []
    seen_families: dict[str, int] = {}

    for meta in sorted(candidates, key=lambda m: m.dataset_id):
        reason = screen_one(meta, require_small=require_small)
        if reason:
            excluded.append(Excluded(dataset_id=meta.dataset_id, name=meta.name, reason=reason))
            continue

        family = family_of(meta.name)
        already = seen_families.get(family, 0)
        if already >= max_per_family:
            excluded.append(
                Excluded(
                    dataset_id=meta.dataset_id,
                    name=meta.name,
                    reason=f"family '{family}' already represented (max {max_per_family})",
                )
            )
            continue

        seen_families[family] = already + 1
        kept.append(meta)

    return Screening(kept=kept, excluded=excluded)


def coverage(kept: list[DatasetMetadata]) -> dict[str, int]:
    """Count how many kept datasets exercise each characteristic the recommender reasons about.

    #8 requires the collection to cover each band. A zero here is a gap the study cannot
    speak to — the sub-500-row case being the one that started this discussion.
    """
    return {
        "rows < 500": sum(1 for m in kept if m.rows < SMALL_BAND_MAX_ROWS),
        "rows 500-10k": sum(1 for m in kept if SMALL_BAND_MAX_ROWS <= m.rows <= 10_000),
        "rows > 10k": sum(1 for m in kept if m.rows > 10_000),
        "classification": sum(1 for m in kept if m.is_classification),
        "regression": sum(1 for m in kept if not m.is_classification),
        "multiclass": sum(1 for m in kept if m.classes > 2),
        "binary": sum(1 for m in kept if m.classes == 2),
        "has missing values": sum(1 for m in kept if m.missing_values > 0),
        "has categorical features": sum(1 for m in kept if m.categorical_features > 1),
    }
