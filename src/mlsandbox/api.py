"""The HTTP surface over the study.

FastAPI rather than a lighter framework for one reason that is specific to this project:
the study's types are already pydantic, so a request schema *is* the class the model was
trained on. D-027's train/serve agreement rests on those types and has failed once
already — a second copy of the schema does not error when it drifts, it predicts (D-037).

Only the health endpoint lives here so far. `/recommend` arrives with 2.2.
"""

from __future__ import annotations

import json
from collections.abc import Callable
from functools import lru_cache
from pathlib import Path
from typing import Annotated

from fastapi import Depends, FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from mlsandbox import (
    artifact,
    characteristics,
    charts,
    detection,
    eda,
    layer1,
    recommend,
    training,
    upload,
)
from mlsandbox.base import StrictModel
from mlsandbox.config import PROJECT_ROOT, load_config
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
from mlsandbox.training_jobs import MethodResult, TrainingJob
from mlsandbox.training_jobs import get as get_job

MAX_TRAINING_METHODS = 5
"""FR-8.4: at most 5 methods train per job."""

MODEL_PATH_PARTS = ("model", "layer2.joblib")
"""Where `scripts/package_model.py` writes the artifact, relative to the data directory."""

CHARACTERISTICS_PATH_PARTS = ("model", "characteristics.json")
"""Where `scripts/package_model.py` writes the method characteristics table."""


def model_path() -> Path:
    return load_config().paths.datasets.parent.joinpath(*MODEL_PATH_PARTS)


def characteristics_path() -> Path:
    return load_config().paths.datasets.parent.joinpath(*CHARACTERISTICS_PATH_PARTS)


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


@lru_cache(maxsize=1)
def get_characteristics() -> dict[str, characteristics.Characteristics]:
    """The method characteristics table, loaded once and kept.

    A different file from the model, on purpose: this is derived data computed by
    `scripts/package_model.py` from the same benchmark run, not something the artifact
    itself needs to answer a recommendation. Loading it separately means a table rebuild
    does not require re-fitting Layer 2, and vice versa.
    """
    path = characteristics_path()
    if not path.exists():
        raise RuntimeError(
            f"No characteristics table at {path}. Run scripts/package_model.py."
        )
    payload = json.loads(path.read_text())
    return {name: characteristics.Characteristics(**row) for name, row in payload.items()}


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


class ColumnInventory(StrictModel):
    """Every feature's name and chart form, target excluded — the feature picker's stock.

    Cheap to compute (a dtype check per column, no aggregation) so the picker can
    paginate a 500-column file before any column's actual distribution is asked for.
    """

    columns: list[eda.ColumnKind]
    total: int


@app.post("/api/dataset/eda/columns")
async def eda_columns(
    file: Annotated[UploadFile, File()], target: Annotated[str, Form()]
) -> ColumnInventory:
    """List the dataset's features and which chart form each gets.

    The file is sent again rather than remembered, the same as every other dataset
    endpoint (FR-7.2) — the server keeps it for the length of this call and no longer.
    """
    parsed = upload.read(await file.read(), filename=file.filename or "")
    if isinstance(parsed, upload.Rejected):
        raise HTTPException(
            status_code=422, detail={"reason": parsed.reason, "message": parsed.message}
        )
    kinds = eda.column_kinds(parsed.frame, target=target)
    return ColumnInventory(columns=kinds, total=len(kinds))


class DistributionsResult(StrictModel):
    target: eda.Histogram | eda.CategoricalBars
    features: list[eda.Histogram | eda.CategoricalBars]


@app.post("/api/dataset/eda/distributions")
async def eda_distributions(
    file: Annotated[UploadFile, File()],
    target: Annotated[str, Form()],
    columns: Annotated[list[str] | None, Form()] = None,
) -> DistributionsResult:
    """Summarise the requested feature columns, plus the target's own distribution.

    Only the columns actually asked for — the feature picker's current page — are
    computed. A 500-column file does not mean 500 histograms cross the wire on every
    request; the picker asks again for the next page.

    **Never a row.** Every summary here is bins and counts (`mlsandbox.eda`), which is
    what makes this endpoint unable to leak one by accident rather than merely
    promising not to.
    """
    parsed = upload.read(await file.read(), filename=file.filename or "")
    if isinstance(parsed, upload.Rejected):
        raise HTTPException(
            status_code=422, detail={"reason": parsed.reason, "message": parsed.message}
        )

    requested = columns or []
    unknown = [c for c in [target, *requested] if c not in parsed.frame.columns]
    if unknown:
        raise HTTPException(
            status_code=422,
            detail={
                "reason": "unknown-column",
                "message": f"Not a column in this file: {', '.join(unknown)}.",
            },
        )

    return DistributionsResult(
        target=eda.summarise_column(parsed.frame[target]),
        features=[eda.summarise_column(parsed.frame[c]) for c in requested],
    )


@app.post("/api/dataset/eda/correlation")
async def eda_correlation(
    file: Annotated[UploadFile, File()], target: Annotated[str, Form()]
) -> eda.CorrelationMatrix:
    """The correlation heatmap's data — top-K numeric features by variance, target
    excluded, K capped at `eda.MAX_CORRELATION_FEATURES`.

    Fewer than two numeric features (including an all-categorical file) is a 200 with
    an empty matrix, not a 422 — there is genuinely nothing to correlate, and that is a
    state for the panel to render rather than a request the server refuses.
    """
    parsed = upload.read(await file.read(), filename=file.filename or "")
    if isinstance(parsed, upload.Rejected):
        raise HTTPException(
            status_code=422, detail={"reason": parsed.reason, "message": parsed.message}
        )
    if target not in parsed.frame.columns:
        raise HTTPException(
            status_code=422,
            detail={"reason": "unknown-column", "message": f"Not a column in this file: {target}."},
        )
    return eda.correlation_matrix(parsed.frame, exclude=target)


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
    table: Annotated[
        dict[str, characteristics.Characteristics], Depends(get_characteristics)
    ],
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
        characteristics=table,
    )


class TrainingStarted(StrictModel):
    job_id: str


@app.post("/api/train")
async def start_training(
    file: Annotated[UploadFile, File()],
    target: Annotated[str, Form()],
    task: Annotated[Task, Form()],
    methods: Annotated[list[str] | None, Form()] = None,
) -> TrainingStarted:
    """Begin training `methods`, in the fit-score order the recommendation already
    showed, on the file the browser just sent again (FR-7.2 — the server keeps it for
    the length of this call and no longer; `training.start` copies only what it needs
    into the background thread it hands off to).

    Everything is validated **before** a subprocess ever starts (D-053's job aborts on
    a fit error, but that is for failures a 422 here cannot see coming — an unknown
    column or a nonexistent method is not one of those, and a user should not wait on a
    process that was always going to fail).
    """
    parsed = upload.read(await file.read(), filename=file.filename or "")
    if isinstance(parsed, upload.Rejected):
        raise HTTPException(
            status_code=422, detail={"reason": parsed.reason, "message": parsed.message}
        )
    if target not in parsed.frame.columns:
        raise HTTPException(
            status_code=422,
            detail={"reason": "unknown-column", "message": f"Not a column in this file: {target}."},
        )
    if not methods:
        raise HTTPException(
            status_code=422,
            detail={"reason": "no-methods", "message": "At least one method is required."},
        )
    if len(methods) > MAX_TRAINING_METHODS:
        raise HTTPException(
            status_code=422,
            detail={
                "reason": "too-many-methods",
                "message": f"At most {MAX_TRAINING_METHODS} methods train per run (FR-8.4).",
            },
        )
    unknown = [name for name in methods if name not in METHODS]
    if unknown:
        raise HTTPException(
            status_code=422,
            detail={
                "reason": "unknown-method",
                "message": f"Not a recognised method: {', '.join(unknown)}.",
            },
        )

    # The study's three-way Task drives the recommendation; `methods.build` only knows
    # the two-way split, the same reduction `recommend.for_problem` already makes.
    ml_task = "regression" if task == "regression" else "classification"
    untrainable = [
        name
        for name in methods
        if not METHODS[name].supports(ml_task) or METHODS[name].implementation != "sklearn"
    ]
    if untrainable:
        raise HTTPException(
            status_code=422,
            detail={
                "reason": "untrainable-method",
                "message": f"Can't be trained here: {', '.join(untrainable)}.",
            },
        )

    # A blank outcome cannot be trained on, the same reason `/api/dataset/detect`
    # (`detection.detect`) drops these rows rather than counting them.
    usable = parsed.frame.dropna(subset=[target])
    features = usable.drop(columns=[target])
    target_values = usable[target].to_numpy()

    # Answered as regression against a column of text or too-broad categories: fitting
    # would fail on the first fold with scikit-learn's own "could not convert string to
    # float", a message that names an implementation detail nobody asked about. Caught
    # here, before any subprocess starts, the same principle as every check above it.
    if ml_task == "regression" and detection.is_categorical_target(usable[target]):
        raise HTTPException(
            status_code=422,
            detail={
                "reason": "not-numeric-for-regression",
                "message": (
                    f"{target} isn't numbers, so it can't be trained on as a number. "
                    "Go back and answer what you're predicting as a category instead."
                ),
            },
        )

    job = training.start(methods, ml_task, features, target_values)
    return TrainingStarted(job_id=job.id)


class MethodStatusOut(StrictModel):
    """`MethodResult`, minus the fitted pipeline — an sklearn `Pipeline` has no JSON
    form, and #4.4/#4.5's own endpoints read it straight from the job registry rather
    than through this one."""

    method: str
    status: str
    mean_score: float | None = None
    std_score: float | None = None
    fold_scores: list[float] = []
    fit_seconds: float | None = None
    detail: str | None = None

    @classmethod
    def of(cls, result: MethodResult) -> MethodStatusOut:
        return cls(
            method=result.method,
            status=result.status,
            mean_score=result.mean_score,
            std_score=result.std_score,
            fold_scores=result.fold_scores,
            fit_seconds=result.fit_seconds,
            detail=result.detail,
        )


class TrainingStatus(StrictModel):
    id: str
    methods: list[str]
    budget_seconds: int
    """The per-method timeout tier this job is running under (FR-8.4) — what the
    frontend's loading estimate multiplies the remaining method count by, rather than
    reimplementing `TIMEOUTS_BY_ROWS` a second time in TypeScript."""
    current: str | None
    halted_early: bool
    aborted: bool
    abort_detail: str | None
    done: bool
    results: dict[str, MethodStatusOut]

    @classmethod
    def of(cls, job: TrainingJob) -> TrainingStatus:
        snapshot = job.snapshot()
        return cls(
            id=snapshot["id"],
            methods=snapshot["methods"],
            budget_seconds=snapshot["budget_seconds"],
            current=snapshot["current"],
            halted_early=snapshot["halted_early"],
            aborted=snapshot["aborted"],
            abort_detail=snapshot["abort_detail"],
            done=snapshot["done"],
            results={
                name: MethodStatusOut.of(result) for name, result in snapshot["results"].items()
            },
        )


def _find_job(job_id: str) -> TrainingJob:
    job = get_job(job_id)
    if job is None:
        raise HTTPException(
            status_code=404,
            detail={"reason": "unknown-job", "message": "No training job with that id."},
        )
    return job


@app.get("/api/train/{job_id}")
def training_status(job_id: str) -> TrainingStatus:
    """Poll a job's progress — which methods are done, running, timed out, or never
    reached because the run halted early or was stopped (FR-8.4)."""
    return TrainingStatus.of(_find_job(job_id))


@app.post("/api/train/{job_id}/stop")
def stop_training(job_id: str) -> TrainingStatus:
    """Ends the currently-running method's subprocess and trains nothing further.

    Whatever methods already completed keep their results — the same principle FR-8.4
    states for a per-method timeout: a partial run is still a run, not a discarded one.
    """
    job = _find_job(job_id)
    training.request_stop(job)
    return TrainingStatus.of(job)


ChartBuilder = Callable[..., StrictModel]
"""`(pipeline, features, target, *, feature_x=None, feature_y=None) -> StrictModel`.
Every builder accepts the two keyword-only overrides — FR-4.3's "swap the selected
features" needs them for a decision boundary — even the ones that ignore them."""

CHART_BUILDERS: dict[str, ChartBuilder] = {
    "linear_regression": charts.linear_regression_charts,
    "logistic_regression": charts.logistic_regression_charts,
    "lda": charts.discriminant_charts,
    "qda": charts.discriminant_charts,
    "knn": charts.knn_charts,
}
"""Which methods #4.4's chart panel covers so far — one entry per sub-issue (#95-#107).
A method missing here has no panel yet, not a bug; `method_charts` reports that as a
plain 422 rather than a 404, since the method and job are both real."""


@app.post("/api/train/{job_id}/{method}/charts")
async def method_charts(
    job_id: str,
    method: str,
    file: Annotated[UploadFile, File()],
    target: Annotated[str, Form()],
    feature_x: Annotated[str | None, Form()] = None,
    feature_y: Annotated[str | None, Form()] = None,
) -> (
    charts.LinearRegressionCharts
    | charts.LogisticRegressionCharts
    | charts.DiscriminantCharts
    | charts.KnnCharts
):
    """The fixed chart set for one already-trained method (FR-4.2).

    Reuses the pipeline `/api/train` already fit — never refits it — so what this draws
    is guaranteed to be the same model the training panel scored (#83's grill-me: fit
    once, chart from it, not a second fit that could quietly disagree). The dataset
    itself is not retained between the two calls (FR-7.2): the browser sends the file
    again here, exactly as it does for every other dataset-touching endpoint, and only
    fresh X/y come out of it.

    `feature_x`/`feature_y` are FR-4.3's "swap the selected features" — ignored by
    every builder except a decision boundary's, which falls back to its own
    auto-selection when they're absent or not a valid pair.
    """
    job = _find_job(job_id)
    builder = CHART_BUILDERS.get(method)
    if builder is None:
        raise HTTPException(
            status_code=422,
            detail={
                "reason": "no-charts-for-method",
                "message": f"No chart panel yet for {method}.",
            },
        )
    result = job.result_for(method)
    if result is None or result.status != "ok" or result.fitted is None:
        raise HTTPException(
            status_code=404,
            detail={
                "reason": "no-fitted-method",
                "message": f"{method} has no completed fit in this job.",
            },
        )

    parsed = upload.read(await file.read(), filename=file.filename or "")
    if isinstance(parsed, upload.Rejected):
        raise HTTPException(
            status_code=422, detail={"reason": parsed.reason, "message": parsed.message}
        )
    if target not in parsed.frame.columns:
        raise HTTPException(
            status_code=422,
            detail={"reason": "unknown-column", "message": f"Not a column in this file: {target}."},
        )

    usable = parsed.frame.dropna(subset=[target])
    features = usable.drop(columns=[target])
    target_values = usable[target].to_numpy()
    return builder(result.fitted, features, target_values, feature_x=feature_x, feature_y=feature_y)


FRONTEND_DIST = PROJECT_ROOT / "app" / "dist"
"""Where `npm run build` (`app/`) writes the frontend's static bundle.

Serving it from this same process is what makes frontend and backend one origin in a
deployment — no CORS to configure, no separate base URL per environment, the same
guarantee the dev-only Vite proxy already gives locally (D-053's cousin: one fewer thing
to differ between the two).

Only registered when the bundle actually exists, so `make dev` (backend alone, frontend
served by its own dev server on :5173) is untouched — this exists for a built deployment,
not for local development.
"""

if FRONTEND_DIST.is_dir():
    app.mount("/assets", StaticFiles(directory=FRONTEND_DIST / "assets"), name="assets")

    @app.get("/{full_path:path}")
    async def spa(full_path: str) -> FileResponse:
        """Every non-API route serves the same `index.html` — react-router-dom (`/`,
        `/benchmark`) decides what that means client-side. Registered last, deliberately:
        Starlette matches routes in declaration order, and every `/api/...` route above
        this one in the file must win before this catch-all ever sees the request.

        A *nonexistent* `/api/...` route still reaches here, though — this matcher is a
        plain path wildcard, not scoped to "whatever `/api` didn't claim". Excluded by
        name rather than left to fall through to `index.html`, which would turn a
        mistyped API call into a 200 of HTML instead of the 404 it should be.
        """
        if full_path.startswith("api/"):
            raise HTTPException(status_code=404)
        candidate = FRONTEND_DIST / full_path
        if full_path and candidate.is_file():
            return FileResponse(candidate)
        return FileResponse(FRONTEND_DIST / "index.html")
