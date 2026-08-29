"""The HTTP surface over the study.

FastAPI rather than a lighter framework for one reason that is specific to this project:
the study's types are already pydantic, so a request schema *is* the class the model was
trained on. D-027's train/serve agreement rests on those types and has failed once
already — a second copy of the schema does not error when it drifts, it predicts (D-037).

Only the health endpoint lives here so far. `/recommend` arrives with 2.2.
"""

from __future__ import annotations

from fastapi import FastAPI

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
