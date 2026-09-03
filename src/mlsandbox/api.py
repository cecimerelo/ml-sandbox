"""The HTTP surface over the study.

FastAPI rather than a lighter framework for one reason that is specific to this project:
the study's types are already pydantic, so a request schema *is* the class the model was
trained on. D-027's train/serve agreement rests on those types and has failed once
already — a second copy of the schema does not error when it drifts, it predicts (D-037).

Only the health endpoint lives here so far. `/recommend` arrives with 2.2.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Annotated

from fastapi import Depends, FastAPI, File, Form, HTTPException, UploadFile

from mlsandbox import artifact, detection, layer1, recommend, upload
from mlsandbox.base import StrictModel
from mlsandbox.config import load_config
from mlsandbox.metafeatures import (
    ClassBalance,
    FeatureBand,
    FeatureTypes,
    MissingLevel,
    RowBand,
    Task,
    from_form,
)
from mlsandbox.methods import METHODS

MODEL_PATH_PARTS = ("model", "layer2.joblib")
"""Where `scripts/package_model.py` writes the artifact, relative to the data directory."""


def model_path() -> Path:
    return load_config().paths.datasets.parent.joinpath(*MODEL_PATH_PARTS)


@lru_cache(maxsize=1)
def get_model() -> artifact.Artifact:
    """The artifact this server answers from, loaded once and kept.

    Once rather than per request: reading it again would spend a hundred milliseconds
    proving something that cannot have changed.

    **On first use rather than at import**, which was the first thing I got wrong here.
    Loading at module level meant `mlsandbox.api` could not be imported at all without a
    model on disk — so CI could not collect the tests, and the upload and detection
    endpoints, which have no use for the model, stopped working without one.

    The concern that led me there is real: a server that starts without its model and
    fails on someone's first request has moved a deployment problem into their session.
    That is answered by `/api/health`, which reports whether the model is loadable, rather
    than by refusing to import.
    """
    path = model_path()
    if not path.exists():
        raise RuntimeError(
            f"No model at {path}. Run scripts/package_model.py — the benchmark has to have "
            "produced results first."
        )
    return artifact.load(path)


app = FastAPI(
    title="ML Sandbox",
    description="An explainable recommender for supervised learning methods.",
)


class Health(StrictModel):
    """Proof the server can reach the study, not merely that it is running.

    A health check that only says "the process is up" passes while the engine is
    unimportable, which is the failure worth catching: the whole design rests on the
    application calling the same code the study measured, rather than a reimplementation
    of it.
    """

    status: str
    methods: int

    model: str
    """`ready` or `missing`.

    Reported here so a deployment can find out before a user does. This is what replaced
    refusing to import without a model: the check happens where someone is looking for it,
    rather than by making the module unusable.
    """


@app.get("/api/health")
def health() -> Health:
    return Health(
        status="ok",
        methods=len(METHODS),
        model="ready" if model_path().exists() else "missing",
    )


class DatasetSummary(StrictModel):
    """What the server will say about an uploaded file.

    A summary, never rows. The endpoint cannot return the user's data because it has no
    field to put it in, which is a better guarantee than remembering not to.
    """

    columns: list[str]
    rows: int
    skipped: list[upload.Skipped] = []


@app.post("/api/dataset")
async def describe_dataset(file: Annotated[UploadFile, File()]) -> DatasetSummary:
    """Validate an uploaded CSV and report its shape.

    **The server does not keep the file.** It is read into memory, described, and dropped
    when the request ends — so the browser holds the only copy and sends it again with the
    next request that needs it.

    The alternative, caching it server-side between requests, means sessions, expiry, and a
    window in which a user's data sits on a machine they do not control. Stateless is more
    work for the client and a far shorter sentence in the privacy notice, which has to be
    true (FR-7.2).
    """
    result = upload.read(await file.read(), filename=file.filename or "")
    if isinstance(result, upload.Rejected):
        # 422 rather than 400: the request was well-formed and the file is not usable. A
        # 400 would say the client got the call wrong, which it did not.
        raise HTTPException(
            status_code=422, detail={"reason": result.reason, "message": result.message}
        )
    return DatasetSummary(columns=result.columns, rows=result.rows, skipped=result.skipped)


class DetectionResult(StrictModel):
    """What the file says about itself, once a target is chosen.

    Exact counts *and* their bands. The counts are facts about the file and read-only; the
    bands are what the engine consumes, and showing both means a user can check the
    reading without being asked to do the banding themselves.
    """

    task: str
    rows: str
    features: str
    feature_types: str
    missing: str
    class_balance: str

    n_rows: int
    n_features: int
    n_classes: int | None = None
    missing_rate: float = 0.0
    dropped_rows: int = 0

    uncertain: list[str] = []


@app.post("/api/dataset/detect")
async def detect_dataset(
    file: Annotated[UploadFile, File()], target: Annotated[str, Form()]
) -> DetectionResult:
    """Read a dataset's properties, given which column is the outcome.

    The file is sent again rather than remembered between requests: the server keeps it for
    the length of one call and no longer, which is what FR-7.2 promises and what the
    privacy notice will say.

    Refusals are 422 with a message naming the column. A target that cannot be predicted is
    not a server error — the file is fine and the choice is not — and the user fixes it by
    picking a different column.
    """
    parsed = upload.read(await file.read(), filename=file.filename or "")
    if isinstance(parsed, upload.Rejected):
        raise HTTPException(
            status_code=422, detail={"reason": parsed.reason, "message": parsed.message}
        )

    result = detection.detect(parsed.frame, target)
    if isinstance(result, detection.Unpredictable):
        raise HTTPException(
            status_code=422, detail={"reason": result.problem, "message": result.message}
        )

    # `regime` is deliberately not sent. It is derived from the row and feature bands
    # (D-028), so the server computes it when the recommendation is asked for; sending it
    # would put a second copy in the browser, and two copies of a derived value are how
    # the two paths come to disagree.
    bands = {
        field: value
        for field, value in result.features.as_row().items()
        if field != "regime"
    }
    return DetectionResult(
        **bands,
        n_rows=result.n_rows,
        n_features=result.n_features,
        n_classes=result.n_classes,
        missing_rate=result.missing_rate,
        dropped_rows=result.dropped_rows,
        uncertain=result.uncertain,
    )


class RecommendationRequest(StrictModel):
    """The form's answers.

    **These are the study's own types**, not a parallel copy of them. `RowBand` and the
    rest are the `Literal`s the model was trained on, so an answer it never saw cannot be
    expressed here — it is rejected at the edge, naming the field, with no validation
    written by hand.

    That matters more here than it usually would: D-027's train/serve agreement rests on
    these types, and it has already failed once. A schema of its own would be a second
    definition of what a valid band is, and when the two drift the model does not error
    (D-037).

    `regime` is absent because it is derived from the row and feature bands, not asked. The
    server computes it, so there is one definition of it rather than two (D-028).
    """

    task: Task
    rows: RowBand
    features: FeatureBand
    feature_types: FeatureTypes
    missing: MissingLevel
    class_balance: ClassBalance

    explainability: layer1.Explainability = "not important"
    suspects_non_linearity: layer1.Suspicion = "no"
    suspects_interactions: layer1.Suspicion = "no"


@app.post("/api/recommend")
def recommend_method(
    request: RecommendationRequest,
    model: Annotated[artifact.Artifact, Depends(get_model)],
) -> recommend.Recommendation:
    """Recommend a method for the problem the form describes.

    The meta-features are built by `from_form`, the same function the study used for its
    no-dataset path, so the model is served exactly what it was trained on.
    """
    features = from_form(
        task=request.task,
        rows=request.rows,
        features=request.features,
        feature_types=request.feature_types,
        missing=request.missing,
        class_balance=request.class_balance,
    )
    return recommend.for_problem(
        features,
        model,
        explainability=request.explainability,
        suspects_non_linearity=request.suspects_non_linearity,
        suspects_interactions=request.suspects_interactions,
    )
