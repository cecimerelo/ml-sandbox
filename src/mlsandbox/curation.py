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

import random
import re

from mlsandbox.base import StrictModel
from mlsandbox.dataset import Dataset

MAX_FEATURES = 500
"""NFR-2. Also removes the image-derived datasets in CC18, whose pixel columns run to 785
and beyond (D-004)."""

MIN_ROWS = 50
"""Below this, 5-fold cross-validation stops being meaningful — folds of fewer than ten
rows produce scores dominated by which rows happened to land where. PMLB goes down to 8
rows, which is a dataset in name only."""

MAX_ROWS = 100_000
"""Revises D-005's "no ceiling", which was decided when the largest candidate had 96k
rows. PMLB reaches a million, and a single dataset that size would consume more of the
compute budget than the entire small band. The tiered timeouts of FR-8.4 bound the worst
case per method; this bounds it per dataset."""

SMALL_BAND_MAX_ROWS = 500
"""FR-1.3's lowest band. Neither curated suite contains anything below this, which is why
D-006 subsamples and D-007 pins real small datasets."""

DEPRECATED_PREFIX = "_deprecated"
"""PMLB marks 35 datasets as deprecated by naming them. Its own authors have withdrawn
them, so including them would mean drawing conclusions from data the maintainers no
longer stand behind."""

SYNTHETIC_MARKERS = ("feynman_", "strogatz_", "_bng_", "bng_")
"""Generated rather than measured, and excluded for the same reason (D-007).

* **Feynman** (119) and **Strogatz** (14) are physics equations used for
  symbolic-regression benchmarking. A third of the collection; admitting them would let
  equation recovery dominate a study about method selection on real tabular data.
* **BNG** (6) are sampled from Bayesian networks fitted to smaller datasets. They are the
  largest things in PMLB — one has a million rows — so they crowd the large-row band
  while describing a generator rather than a phenomenon. Five of six had entered the
  sample, taking a quarter of that band.
"""

IMAGE_DERIVED = frozenset({"mnist_784", "Fashion-MNIST", "Devnagari-Script", "CIFAR_10"})
"""Datasets whose columns are flattened pixels. The feature cap already removes these;
naming them makes the intent explicit rather than incidental, and catches any that would
otherwise slip under the cap."""


class Excluded(StrictModel):
    name: str
    reason: str


class Screening(StrictModel):
    kept: list[Dataset]
    excluded: list[Excluded]

    @property
    def total(self) -> int:
        return len(self.kept) + len(self.excluded)


def screen_one(meta: Dataset, *, require_small: bool = False) -> str | None:
    """Return why this dataset is excluded, or None if it is kept.

    `require_small` applies to the pinned candidates of D-007, which earn their place only
    by covering the sub-500-row band the curated suites lack. A dataset above that
    threshold is not rejected for being poor — it is simply already covered.
    """
    if meta.name.lower().startswith(DEPRECATED_PREFIX):
        return "deprecated by the source"
    lowered = meta.name.lower()
    if any(marker.strip("_") in lowered for marker in SYNTHETIC_MARKERS):
        return "synthetic: generated, not measured"
    if meta.name in IMAGE_DERIVED:
        return "image-derived: out of scope per NFR-2"
    if meta.predictors > MAX_FEATURES:
        return f"{meta.predictors} features exceeds the {MAX_FEATURES} cap (NFR-2)"
    if meta.rows == 0:
        return "no reported row count: metadata incomplete"
    if meta.rows < MIN_ROWS:
        return f"{meta.rows} rows is below {MIN_ROWS}: too few for meaningful folds"
    if meta.rows > MAX_ROWS:
        return f"{meta.rows} rows exceeds the {MAX_ROWS} compute ceiling"
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
    candidates: list[Dataset],
    *,
    require_small: bool = False,
    max_per_family: int = 1,
) -> Screening:
    """Apply the selection rules in a stable order.

    Family de-duplication runs after the per-dataset rules, so a family is never
    represented by a member that would have been excluded on its own merits.
    """
    kept: list[Dataset] = []
    excluded: list[Excluded] = []
    seen_families: dict[str, int] = {}

    for meta in sorted(candidates, key=lambda m: m.name):
        reason = screen_one(meta, require_small=require_small)
        if reason:
            excluded.append(Excluded(name=meta.name, reason=reason))
            continue

        family = family_of(meta.name)
        already = seen_families.get(family, 0)
        if already >= max_per_family:
            excluded.append(
                Excluded(
                    name=meta.name,
                    reason=f"family '{family}' already represented (max {max_per_family})",
                )
            )
            continue

        seen_families[family] = already + 1
        kept.append(meta)

    return Screening(kept=kept, excluded=excluded)


def coverage(kept: list[Dataset]) -> dict[str, int]:
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
        # Guarded on is_classification: PMLB does not zero n_classes for regression, so
        # counting on classes alone silently files regression datasets as multiclass.
        "multiclass": sum(1 for m in kept if m.is_classification and m.classes > 2),
        "binary": sum(1 for m in kept if m.is_classification and m.classes == 2),
        # `None` means the source does not report it. PMLB's datasets are pre-cleaned and
        # carry no missing-value count, so this band cannot be covered from PMLB alone —
        # the same shape of gap as the sub-500-row one.
        "has missing values": sum(1 for m in kept if (m.missing_values or 0) > 0),
        "missing-value data unavailable": sum(1 for m in kept if m.missing_values is None),
        "has categorical features": sum(1 for m in kept if m.categorical_predictors > 0),
    }


def stratified_sample(
    kept: list[Dataset],
    *,
    per_stratum: int,
    seed: int,
) -> Screening:
    """Reduce the collection to `per_stratum` datasets per size-band × task-type cell.

    The full screened collection is larger than the compute budget allows (D-011), so it
    is sampled rather than truncated. Stratifying on the two characteristics the
    recommender reasons about most — sample size and task type — keeps every band
    populated, which a simple head-of-list cut would not.

    Selection within a stratum is by seeded shuffle, not by any property of the dataset:
    picking "the easiest N" or "the smallest N" would bias the study in a way nobody
    could see afterwards.
    """
    rng = random.Random(seed)
    strata: dict[tuple[str, str], list[Dataset]] = {}
    for dataset in sorted(kept, key=lambda d: d.name):
        band = (
            "small"
            if dataset.rows < SMALL_BAND_MAX_ROWS
            else "medium"
            if dataset.rows <= 10_000
            else "large"
        )
        task = "classification" if dataset.is_classification else "regression"
        strata.setdefault((band, task), []).append(dataset)

    sampled: list[Dataset] = []
    dropped: list[Excluded] = []
    for stratum in sorted(strata):
        members = strata[stratum][:]
        rng.shuffle(members)
        sampled.extend(members[:per_stratum])
        dropped.extend(
            Excluded(
                name=d.name,
                reason=f"not sampled: stratum {stratum[0]}/{stratum[1]} already has "
                f"{per_stratum}",
            )
            for d in members[per_stratum:]
        )

    return Screening(
        kept=sorted(sampled, key=lambda d: d.name),
        excluded=sorted(dropped, key=lambda e: e.name),
    )
