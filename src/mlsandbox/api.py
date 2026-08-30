"""The HTTP surface over the study.

FastAPI rather than a lighter framework for one reason that is specific to this project:
the study's types are already pydantic, so a request schema *is* the class the model was
trained on. D-027's train/serve agreement rests on those types and has failed once
already — a second copy of the schema does not error when it drifts, it predicts (D-037).

Only the health endpoint lives here so far. `/recommend` arrives with 2.2.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import FastAPI, File, HTTPException, UploadFile

from mlsandbox import upload
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
    skipped: list[str] = []


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
