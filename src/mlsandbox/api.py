"""The HTTP surface over the study.

FastAPI rather than a lighter framework for one reason that is specific to this project:
the study's types are already pydantic, so a request schema *is* the class the model was
trained on. D-027's train/serve agreement rests on those types and has failed once
already — a second copy of the schema does not error when it drifts, it predicts (D-037).

Only the health endpoint lives here so far. `/recommend` arrives with 2.2.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import FastAPI, File, Form, HTTPException, UploadFile

from mlsandbox import detection, upload
from mlsandbox.base import StrictModel
from mlsandbox.methods import METHODS

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


@app.get("/api/health")
def health() -> Health:
    return Health(status="ok", methods=len(METHODS))


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
