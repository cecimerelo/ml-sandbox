"""Packaging Layer 2 so the application can load it.

The application imports `mlsandbox` (D-037), so this is not a cross-language export
problem — the artifact is a fitted pipeline plus the facts needed to say what it is.

**Those facts are the point.** A model file looks identical whether it was trained on the
whole collection or on however much of it had finished, and the difference does not surface
as an error: it surfaces as a recommendation slightly worse than the thesis claims. So the
artifact carries its own provenance and says when it is provisional, and a half-trained
model cannot ship quietly.
"""

from __future__ import annotations

import json
import platform
from datetime import UTC, datetime
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import sklearn

from mlsandbox import layer2
from mlsandbox.base import StrictModel
from mlsandbox.metafeatures import MetaFeatures

ARTIFACT_VERSION = 1
"""Bumped when the artifact's shape changes.

A load that accepts a file of a different shape does not fail — it answers, and the answers
are wrong in a way nothing downstream checks. The version is what turns that into an error.
"""


class ModelCard(StrictModel):
    """What this model is, in the form a reader needs before trusting a number from it."""

    version: int
    created: str

    datasets: int
    """How many datasets the model saw."""

    collection_size: int
    """How many the collection holds, as the manifest said at packaging time.

    Read from a file that changes between branches, which is how a model trained on sixty
    datasets first announced itself as complete while the collection had grown to a
    hundred and six. `unknown_datasets` is the guard that does not depend on it.
    """

    unknown_datasets: int = 0
    """Datasets in the results that the manifest does not list.

    Any at all means the two disagree about what the collection is, and the count above
    cannot be trusted — the results were produced against a different manifest from the one
    being read now. Cheap to compute and it does not rely on remembering which branch is
    checked out.
    """

    observations: int
    """(dataset, method) pairs in the training table."""

    methods: int
    missing_rate: float
    seed: int
    python: str
    sklearn: str

    answer_support: dict[str, dict[str, int]] = {}
    """How many training datasets carry each answer, per meta-feature.

    The artifact's only means of saying *"I have not seen data like this"*. Kept in the card
    rather than recomputed, because the answer depends on what the model was trained on and
    not on whatever manifest happens to be on disk.
    """

    @property
    def is_provisional(self) -> bool:
        """True when this model should not be reported from.

        Either the benchmark had not finished, or the manifest and the results disagree
        about which datasets exist — in which case `collection_size` is describing a
        different collection and "complete" would be a claim about the wrong thing.

        Reported rather than prevented. Building the application against a partial model is
        reasonable, and packaging one is how you find out the pipeline works — shipping one
        without noticing is the failure, and the way to avoid it is to make the artifact say
        so everywhere it is used.
        """
        return self.datasets < self.collection_size or self.unknown_datasets > 0

    def summary(self) -> str:
        state = "PROVISIONAL" if self.is_provisional else "complete"
        if self.unknown_datasets:
            state = f"PROVISIONAL ({self.unknown_datasets} datasets not in the manifest)"
        return (
            f"Layer 2 v{self.version} — {state}: {self.datasets}/{self.collection_size} "
            f"datasets, {self.observations} observations, {self.methods} methods, "
            f"seed {self.seed}, scikit-learn {self.sklearn}"
        )


class Support(StrictModel):
    """How well the training data covers one problem.

    Reported alongside the ranking, because the model's own uncertainty does not carry this
    and was measured not to: the spread across a forest's trees tracks how *hard* a region
    is, not how *unfamiliar*. A rare combination came back more confident than a typical
    one when this was checked, so treating tree spread as a novelty signal would have been
    a confident wrong answer with a number attached to it — the outcome #17 forbids.
    """

    field: str
    answer: str
    datasets: int
    """Training datasets sharing the least-supported answer given."""

    total: int

    @property
    def is_extrapolating(self) -> bool:
        """No training dataset answered this way. The ranking is a guess."""
        return self.datasets == 0

    def sentence(self) -> str:
        if self.is_extrapolating:
            return (
                f"No dataset in the study had {self.field} = {self.answer!r}, so this "
                "ranking is extrapolated rather than learned."
            )
        return (
            f"{self.datasets} of {self.total} datasets had {self.field} = "
            f"{self.answer!r} — the least-supported answer given."
        )


class Artifact(StrictModel):
    """A fitted model and the card that describes it, kept together.

    Together rather than beside each other, because a card that can be separated from its
    model is a card that will eventually describe a different one.
    """

    model: object
    card: ModelCard

    model_config = {"arbitrary_types_allowed": True, "frozen": True}

    def support(self, features: MetaFeatures) -> Support:
        """The thinnest evidence behind this problem.

        The weakest single answer rather than the exact combination: with three options
        across six questions there are 729 combinations and roughly a hundred datasets, so
        almost every combination is unseen — including entirely ordinary ones. A measure
        that fires on everything says nothing.
        """
        counts = self.card.answer_support
        total = self.card.datasets
        weakest = min(
            (
                (counts.get(field, {}).get(answer, 0), field, answer)
                for field, answer in features.as_row().items()
                if field in counts
            ),
            default=(total, "", ""),
        )
        return Support(field=weakest[1], answer=weakest[2], datasets=weakest[0], total=total)

    def rank(self, features: MetaFeatures, methods: list[str]) -> list[layer2.Prediction]:
        """Order the candidate methods for one problem, best first.

        One call for both paths: the meta-features arrive identically whether computed from
        an uploaded dataset or taken from the form (D-027), which is what makes the
        form-only path work at all rather than being a second implementation of this one.
        """
        return layer2.rank_methods(self.model, features, methods)


def build(
    results: pd.DataFrame,
    metafeatures: pd.DataFrame,
    *,
    seed: int,
    collection_size: int,
    known_datasets: set[str] | None = None,
    missing_rate: float = 0.0,
) -> Artifact:
    """Fit Layer 2 on everything available and record what that was.

    `known_datasets` is what the manifest lists. Given it, the card can say whether the
    results were produced against this manifest or another one, which the size alone
    cannot.
    """
    table = layer2.build_training_table(results, metafeatures, missing_rate=missing_rate)
    model = layer2.build_model(seed)
    model.fit(table.frame, table.target)

    frame = table.frame
    return Artifact(
        model=model,
        card=ModelCard(
            version=ARTIFACT_VERSION,
            created=datetime.now(UTC).isoformat(timespec="seconds"),
            datasets=int(pd.Series(table.groups).nunique()),
            collection_size=collection_size,
            observations=len(frame),
            methods=int(frame[layer2.METHOD_COLUMN].nunique()),
            # Counted against the **results**, not the training table. The table is
            # produced by an inner join with the meta-features, which silently drops any
            # dataset the manifest does not describe — so checking it there compares the
            # manifest with a set already filtered to match it, and always agrees. That is
            # how a model trained on sixty datasets first reported itself complete while
            # twenty more sat in the results.
            unknown_datasets=(
                len(set(results.dataset.unique()) - known_datasets)
                if known_datasets is not None
                else 0
            ),
            # Every meta-feature column, by name rather than by dtype: pandas reports
            # string columns as `object` on one backend and `str` on another, and a check
            # that depends on which one is installed silently produced an empty table.
            answer_support={
                field: metafeatures[field].value_counts().to_dict()
                for field in MetaFeatures.model_fields
                if field in metafeatures.columns
            },
            missing_rate=missing_rate,
            seed=seed,
            python=platform.python_version(),
            sklearn=sklearn.__version__,
        ),
    )


def save(artifact: Artifact, path: Path) -> None:
    """Write the model and its card, and the card again as readable JSON.

    The JSON is not what `load` reads. It is there so a person can answer *"what is this
    file?"* without importing anything — the question asked most often, and the one a
    pickle answers worst.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump({"model": artifact.model, "card": artifact.card.model_dump()}, path)
    path.with_suffix(".json").write_text(
        json.dumps(artifact.card.model_dump(), indent=2) + "\n", encoding="utf-8"
    )


def load(path: Path) -> Artifact:
    """Read an artifact, refusing one written by a different version."""
    payload = joblib.load(path)
    card = ModelCard(**payload["card"])
    if card.version != ARTIFACT_VERSION:
        raise ValueError(
            f"{path.name} is artifact version {card.version}, this code reads "
            f"{ARTIFACT_VERSION}. Regenerate it with scripts/package_model.py."
        )
    return Artifact(model=payload["model"], card=card)


def uncertainty_of(predictions: list[layer2.Prediction]) -> float:
    """How unsure the model is about this problem, as one number.

    The mean spread across the forest's trees. Used to check that unfamiliar problems come
    back less confident — the property #17 asks for, and one that has to be measured rather
    than assumed, because nothing in the model guarantees it.
    """
    return float(np.mean([p.uncertainty for p in predictions])) if predictions else 0.0
