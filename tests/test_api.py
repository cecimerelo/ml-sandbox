"""The HTTP surface.

Thin for now — the health endpoint and the property that makes it worth having.
"""

import time

import numpy as np
import pandas as pd
import pytest
from fastapi.testclient import TestClient

from mlsandbox import artifact
from mlsandbox.api import app, get_characteristics, get_model
from mlsandbox.characteristics import from_benchmark
from mlsandbox.methods import METHODS
from mlsandbox.training_jobs import _REGISTRY

client = TestClient(app)

SYNTHETIC_FEATURES = dict(
    task="binary classification",
    rows="500-10k",
    features="10-50",
    regime="moderate",
    feature_types="numeric",
    missing="none",
    class_balance="roughly equal",
)


def _synthetic_results() -> tuple[pd.DataFrame, pd.DataFrame]:
    """Results and meta-features for a small collection, shared by the model and the
    characteristics table so the two are never built from different data."""
    rng = np.random.default_rng(0)
    methods = ["random_forest", "logistic_regression", "knn", "ridge", "mlp", "decision_tree"]
    rows, meta = [], []
    for i in range(12):
        name = f"d{i}"
        meta.append({"dataset": name, **SYNTHETIC_FEATURES})
        for method in methods:
            good = method == "mlp"
            for fold in range(3):
                rows.append(
                    {
                        "dataset": name,
                        "method": method,
                        "task": "binary classification",
                        "score": (0.9 if good else 0.5) + rng.normal(0, 0.01),
                        "status": "ok",
                        "fit_seconds": 1.0,
                        "missing_rate": 0.0,
                        "fold": fold,
                    }
                )
    return pd.DataFrame(rows), pd.DataFrame(meta)


def _synthetic_model() -> artifact.Artifact:
    """A small artifact, so these tests do not need a benchmark run.

    The endpoint used to load the real model at import, which meant the module could not be
    imported without one — CI could not even collect these tests. Injecting the model is
    what makes the dependency explicit instead of ambient.
    """
    results, meta = _synthetic_results()
    return artifact.build(results, meta, seed=0, collection_size=12)


def _synthetic_characteristics():
    results, _ = _synthetic_results()
    return from_benchmark(results)


# Injected rather than read from disk, so a test failure means the endpoint is wrong and
# not that somebody has not run the benchmark.
app.dependency_overrides[get_model] = _synthetic_model
app.dependency_overrides[get_characteristics] = _synthetic_characteristics


def test_health_reports_ok():
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_health_says_whether_the_model_is_there():
    """So a deployment finds out before a user does.

    This replaced refusing to import without a model: the check happens where someone is
    looking for it, rather than by making the module unusable.
    """
    assert client.get("/api/health").json()["model"] in {"ready", "missing"}


def test_health_proves_the_server_can_reach_the_study():
    """Not merely that the process is up.

    The whole design rests on the application calling the same code the study measured. A
    health check that passes while the engine is unimportable hides exactly that failure.
    """
    assert client.get("/api/health").json()["methods"] == len(METHODS)


def test_an_unknown_route_is_a_404_not_a_crash():
    assert client.get("/api/nope").status_code == 404


# Serving the built frontend (deployment) — skipped unless `npm run build` has produced
# app/dist, the same pattern tests/test_upload.py uses for scripts/make_examples.py's
# generated files: these exercise a built artifact, not something pytest builds itself.


def test_a_client_side_route_still_serves_the_app():
    from mlsandbox.api import FRONTEND_DIST

    if not FRONTEND_DIST.is_dir():
        pytest.skip("app/dist not built — run npm run build in app/")
    # react-router-dom, not the server, decides what "/benchmark" means — the server's
    # only job is to hand back the same index.html it would for "/".
    response = client.get("/benchmark")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")


def test_an_unknown_api_route_is_still_404_even_with_the_frontend_built():
    from mlsandbox.api import FRONTEND_DIST

    if not FRONTEND_DIST.is_dir():
        pytest.skip("app/dist not built — run npm run build in app/")
    # The SPA catch-all is a plain path wildcard, not scoped to "whatever /api/ didn't
    # claim" — without excluding /api/ by name, a mistyped API call would 200 with HTML.
    assert client.get("/api/nope").status_code == 404


# Uploading a dataset


def upload_csv(content: bytes, name: str = "data.csv"):
    return client.post("/api/dataset", files={"file": (name, content, "text/csv")})


def test_a_usable_csv_is_described():
    response = upload_csv(b"a,b\n1,2\n3,4\n")
    assert response.status_code == 200
    assert response.json() == {"columns": ["a", "b"], "rows": 2, "skipped": []}


def test_the_response_has_no_field_that_could_carry_the_data():
    """A summary, never rows.

    The endpoint cannot return the user's data because there is nowhere to put it, which
    is a better guarantee than remembering not to.
    """
    body = upload_csv(b"a,b\n1,2\n").json()
    assert set(body) == {"columns", "rows", "skipped"}


def test_an_unusable_file_is_422_with_a_reason_and_a_message():
    # 422 rather than 400: the request was well-formed and the file is not usable. A 400
    # would say the client got the call wrong, which it did not.
    response = upload_csv(b"\x89PNG not a csv", "photo.png")
    assert response.status_code == 422
    body = response.json()["detail"]
    assert body["reason"] == "not-a-csv"
    assert "comma-separated" in body["message"]


def test_skipped_columns_carry_their_reason():
    # The picker shows them disabled with the reason rather than hiding them, so the reason
    # has to reach the browser.
    notes = "\n".join(f"note {i},{i},{i}" for i in range(10))
    body = upload_csv(f"notes,x,y\n{notes}\n".encode()).json()
    assert body["skipped"][0]["column"] == "notes"
    assert body["skipped"][0]["reason"] == "free-text"
    assert body["skipped"][0]["message"]


def test_a_missing_file_is_rejected_by_the_framework():
    assert client.post("/api/dataset").status_code == 422


# Detecting a dataset's properties


def detect(target: str, name: str = "houses.csv"):
    from mlsandbox.config import PROJECT_ROOT

    content = (PROJECT_ROOT / "examples" / name).read_bytes()
    return client.post(
        "/api/dataset/detect",
        files={"file": (name, content, "text/csv")},
        data={"target": target},
    )


def test_a_numeric_target_is_read_as_regression():
    body = detect("price").json()
    assert body["task"] == "regression"
    assert body["class_balance"] == "not applicable"


def test_a_label_target_is_read_as_classification():
    body = detect("city").json()
    assert body["task"] == "multiclass classification"
    assert body["n_classes"] == 4


def test_the_response_carries_exact_counts_beside_their_bands():
    """Both, because they answer different questions.

    The counts let a user check the reading against their file; the bands are what the
    engine consumes. Showing only the bands would ask them to do the banding themselves to
    verify it.
    """
    body = detect("price").json()
    assert body["n_rows"] == 388
    assert body["rows"] == "<500"


def test_rows_with_no_outcome_are_dropped_and_reported():
    # houses.csv has twelve blank prices. They cannot be trained on, and a row count that
    # still included them would describe a dataset that will not be used.
    body = detect("price").json()
    assert body["dropped_rows"] == 12
    assert body["n_rows"] == 388


def test_the_regime_is_not_sent():
    """Derived from the row and feature bands, so the server computes it when the
    recommendation is asked for. A second copy in the browser is how two paths come to
    disagree about a derived value (D-028)."""
    assert "regime" not in detect("price").json()


def test_an_unpredictable_target_is_422_naming_the_column():
    # A target that cannot be predicted is not a server error: the file is fine and the
    # choice is not, and the user fixes it by picking another column.
    response = detect("agent_note", "houses-with-notes.csv")
    assert response.status_code == 422


def test_a_target_that_is_not_a_column_says_so():
    response = detect("nonexistent")
    assert response.status_code == 422
    assert "nonexistent" in response.json()["detail"]["message"]


# The EDA block


def _houses() -> bytes:
    from mlsandbox.config import PROJECT_ROOT

    return (PROJECT_ROOT / "examples" / "houses.csv").read_bytes()


def eda_columns(target: str = "price"):
    return client.post(
        "/api/dataset/eda/columns",
        files={"file": ("houses.csv", _houses(), "text/csv")},
        data={"target": target},
    )


def eda_distributions(columns: list[str], target: str = "price"):
    return client.post(
        "/api/dataset/eda/distributions",
        files={"file": ("houses.csv", _houses(), "text/csv")},
        data={"target": target, "columns": columns},
    )


def test_the_column_inventory_excludes_the_target():
    body = eda_columns().json()
    assert "price" not in [c["column"] for c in body["columns"]]
    assert body["total"] == len(body["columns"]) == 4


def test_the_column_inventory_names_each_column_s_chart_form():
    body = eda_columns().json()
    kinds = {c["column"]: c["kind"] for c in body["columns"]}
    assert kinds["size_m2"] == "numeric"
    assert kinds["city"] == "categorical"


def test_distributions_are_computed_only_for_the_requested_columns():
    body = eda_distributions(["size_m2"]).json()
    assert [f["column"] for f in body["features"]] == ["size_m2"]


def test_the_target_s_own_distribution_is_always_included():
    body = eda_distributions([]).json()
    assert body["target"]["column"] == "price"


def test_a_numeric_feature_is_a_histogram():
    body = eda_distributions(["size_m2"]).json()
    feature = body["features"][0]
    assert feature["kind"] == "numeric"
    assert sum(b["count"] for b in feature["bins"]) == 400


def test_a_categorical_feature_is_bars():
    body = eda_distributions(["city"]).json()
    feature = body["features"][0]
    assert feature["kind"] == "categorical"
    assert sum(c["count"] for c in feature["categories"]) == 400


def test_neither_endpoint_can_return_a_row():
    """The privacy claim, checked against the actual response shape rather than
    promised: nothing on either endpoint carries a field wide enough for a row."""
    columns_body = eda_columns().json()
    assert set(columns_body) == {"columns", "total"}
    assert set(columns_body["columns"][0]) == {"column", "kind"}

    dist_body = eda_distributions(["size_m2", "city"]).json()
    assert set(dist_body) == {"target", "features"}


def test_an_unknown_column_is_422_naming_it():
    response = eda_distributions(["not_a_real_column"])
    assert response.status_code == 422
    assert "not_a_real_column" in response.json()["detail"]["message"]


def test_an_unknown_target_is_422_naming_it():
    response = eda_distributions([], target="not_a_real_column")
    assert response.status_code == 422
    assert "not_a_real_column" in response.json()["detail"]["message"]


def eda_correlation(target: str = "price"):
    return client.post(
        "/api/dataset/eda/correlation",
        files={"file": ("houses.csv", _houses(), "text/csv")},
        data={"target": target},
    )


def test_correlation_excludes_the_target():
    body = eda_correlation().json()
    assert "price" not in body["features"]


def test_correlation_is_a_real_matrix():
    body = eda_correlation().json()
    n = len(body["features"])
    assert len(body["values"]) == n
    assert all(len(row) == n for row in body["values"])
    for i in range(n):
        assert body["values"][i][i] == pytest.approx(1.0)


def test_correlation_never_carries_a_raw_row():
    body = eda_correlation().json()
    assert set(body) == {"features", "values", "total_numeric"}


def test_correlation_target_that_is_not_a_column_says_so():
    response = eda_correlation(target="not_a_real_column")
    assert response.status_code == 422
    assert "not_a_real_column" in response.json()["detail"]["message"]


# Recommending a method


FORM = dict(
    task="binary classification",
    rows="500-10k",
    features="10-50",
    feature_types="numeric",
    missing="none",
    class_balance="roughly equal",
)


def ask(**overrides):
    return client.post("/api/recommend", json={**FORM, **overrides})


def test_a_valid_form_gets_a_recommendation():
    body = ask().json()
    assert body["recommended"]["method"]
    assert body["recommended"]["label"]
    assert len(body["alternatives"]) == 3


def test_every_suggestion_carries_its_characteristics_row():
    """The comparison table's fields travel with each candidate rather than needing a
    second call, so the panel can render the table without another round trip."""
    body = ask().json()
    row = body["recommended"]["characteristics"]
    assert row["method"] == body["recommended"]["method"]
    for axis in (
        "interpretability",
        "handles_non_linearity",
        "handles_missing_values",
        "accuracy_potential",
        "training_speed",
    ):
        assert row[axis]["word"]
        assert row[axis]["step"] in (1, 2, 3)


def test_the_request_schema_is_the_study_s_own_types():
    """Not a parallel copy of them.

    D-027's train/serve agreement rests on these types and has already failed once. A
    schema of its own would be a second definition of what a valid band is, and when two
    definitions drift the model does not error — it answers (D-037).
    """
    from mlsandbox.api import RecommendationRequest
    from mlsandbox.metafeatures import MetaFeatures

    for field in ("task", "rows", "features", "feature_types", "missing", "class_balance"):
        assert (
            RecommendationRequest.model_fields[field].annotation
            is MetaFeatures.model_fields[field].annotation
        )


def test_an_answer_the_model_never_saw_is_rejected_naming_the_field():
    response = ask(rows="a few thousand")
    assert response.status_code == 422
    assert any("rows" in str(e.get("loc", "")) for e in response.json()["detail"])


def test_the_regime_is_not_asked_for():
    """Derived from the row and feature bands, so the server computes it and there is one
    definition rather than two (D-028)."""
    from mlsandbox.api import RecommendationRequest

    assert "regime" not in RecommendationRequest.model_fields


def test_an_unexpected_field_is_refused_rather_than_ignored():
    assert ask(regime="moderate").status_code == 422


def test_uncertainty_survives_the_trip():
    """#15's central risk is a meta-model trained on around a hundred datasets. Without
    this the interface presents a decisive ranking it has no grounds for."""
    body = ask().json()
    assert body["recommended"]["uncertainty"] >= 0
    for alternative in body["alternatives"]:
        assert alternative["uncertainty"] >= 0


def test_every_suggestion_carries_its_reasons():
    """FR-2.2 needs the decision factors, and a score cannot be turned back into the
    reasoning that produced it."""
    body = ask(suspects_non_linearity="yes").json()
    assert body["recommended"]["reasons"]
    assert all(isinstance(r, str) for r in body["recommended"]["reasons"])


def test_the_reasons_name_no_source():
    # FR-2.3. The theory is a statistical learning course; the interface never says so.
    body = ask(explainability="critical").json()
    for reason in body["recommended"]["reasons"]:
        assert "ISLR" not in reason
        assert "textbook" not in reason.lower()


# The user's constraints


def test_a_constraint_changes_the_answer():
    """A control whose options change nothing is worse than not asking (D-042)."""
    relaxed = ask().json()["recommended"]["method"]
    strict = ask(explainability="critical").json()["recommended"]["method"]
    assert relaxed != strict


def test_a_ruled_out_method_is_returned_rather_than_dropped():
    """Withholding the best method silently leaves the user unable to see what their
    constraint cost them (D-035)."""
    body = ask(explainability="critical").json()
    assert body["excluded"]
    assert all(m["excluded_by_constraint"] for m in body["excluded"])


def test_the_cost_of_a_constraint_is_visible():
    """The number that makes the trade the user's to make, rather than the tool's."""
    body = ask(explainability="critical").json()
    best_allowed = body["recommended"]["expected_shortfall"]
    best_excluded = min(m["expected_shortfall"] for m in body["excluded"])
    assert best_excluded < best_allowed


def test_nothing_is_marked_excluded_when_nothing_is_constrained():
    body = ask().json()
    assert body["excluded"] == []
    assert not body["recommended"]["excluded_by_constraint"]


# What the study knows about a problem like this


def test_the_response_says_how_much_evidence_backs_it():
    """The model's own uncertainty does not carry this and was measured not to: tree
    spread tracks how hard a region is, not how unfamiliar (#17)."""
    support = ask().json()["support"]
    assert support["total"] > 0
    assert support["field"]


def test_an_answer_no_dataset_gave_is_reported_as_extrapolation():
    """The strongest form of the signal: not thin evidence, none."""
    support = ask(missing="a lot").json()["support"]
    assert support["field"] == "missing"
    assert support["datasets"] == 0


def test_the_response_says_when_the_model_is_provisional():
    """A model trained on part of the collection is useful to build against and must never
    be mistaken for the finished one."""
    assert ask().json()["provisional"] is False


# Training the recommended methods on the user's own data (#81)


@pytest.fixture(autouse=True)
def clean_training_registry():
    _REGISTRY.clear()
    yield
    _REGISTRY.clear()


def train(methods: list[str], target: str = "price", task: str = "regression"):
    return client.post(
        "/api/train",
        files={"file": ("houses.csv", _houses(), "text/csv")},
        data={"target": target, "task": task, "methods": methods},
    )


def train_file(name: str, methods: list[str], target: str = "price", task: str = "regression"):
    from mlsandbox.config import PROJECT_ROOT

    content = (PROJECT_ROOT / "examples" / name).read_bytes()
    return client.post(
        "/api/train",
        files={"file": (name, content, "text/csv")},
        data={"target": target, "task": task, "methods": methods},
    )


def wait_until_done(job_id: str, timeout: float = 60.0) -> dict:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        body = client.get(f"/api/train/{job_id}").json()
        if body["done"]:
            return body
        time.sleep(0.2)
    raise AssertionError(f"job {job_id} did not finish within {timeout}s")


def test_training_two_real_methods_on_a_real_dataset_end_to_end():
    job_id = train(["linear_regression", "decision_tree"]).json()["job_id"]

    status = wait_until_done(job_id)

    assert not status["aborted"]
    for method in ["linear_regression", "decision_tree"]:
        assert status["results"][method]["status"] == "ok"
        assert status["results"][method]["mean_score"] is not None


def test_strong_signal_houses_actually_has_signal_to_find():
    # houses.csv's price is pure noise by construction (scripts/make_examples.py),
    # deliberately independent of every other column — the right fixture for exercising
    # the upload path, the wrong one for showing a trained method finds anything.
    # strong-signal-houses.csv prices each row from its own columns, so a method that
    # can't beat guessing the average here would be a real regression, not the dataset.
    job_id = train_file("strong-signal-houses.csv", ["linear_regression"]).json()["job_id"]
    status = wait_until_done(job_id)

    assert status["results"]["linear_regression"]["mean_score"] > 0.9


def test_linear_regression_demo_actually_has_signal_to_find():
    job_id = train_file(
        "linear-regression-demo.csv", ["linear_regression"], target="price"
    ).json()["job_id"]
    status = wait_until_done(job_id)

    assert status["results"]["linear_regression"]["mean_score"] > 0.9


def test_binary_sales_actually_has_signal_to_find():
    job_id = train_file(
        "binary-sales.csv",
        ["logistic_regression"],
        target="sold",
        task="binary classification",
    ).json()["job_id"]
    status = wait_until_done(job_id)

    assert status["results"]["logistic_regression"]["mean_score"] > 0.7


def test_the_status_carries_the_timeout_tier_the_frontend_estimates_from():
    # houses.csv is well under 500 rows — the smallest tier (FR-8.4).
    job_id = train(["linear_regression"]).json()["job_id"]
    status = client.get(f"/api/train/{job_id}").json()
    assert status["budget_seconds"] == 60


def test_an_unknown_target_column_is_422_before_any_job_starts():
    response = train(["linear_regression"], target="not_a_column")
    assert response.status_code == 422
    assert "not_a_column" in response.json()["detail"]["message"]


def test_no_methods_is_422():
    response = train([])
    assert response.status_code == 422
    assert response.json()["detail"]["reason"] == "no-methods"


def test_more_than_five_methods_is_422():
    response = train(["linear_regression"] * 6)
    assert response.status_code == 422
    assert response.json()["detail"]["reason"] == "too-many-methods"


def test_an_unrecognised_method_name_is_422():
    response = train(["not_a_real_method"])
    assert response.status_code == 422
    assert response.json()["detail"]["reason"] == "unknown-method"
    assert "not_a_real_method" in response.json()["detail"]["message"]


def test_a_method_that_does_not_support_the_task_is_422():
    # logistic_regression only supports classification; price is a regression target.
    response = train(["logistic_regression"])
    assert response.status_code == 422
    assert response.json()["detail"]["reason"] == "untrainable-method"


def test_regression_against_a_text_target_is_422_not_a_raw_sklearn_crash():
    # "sold" is "yes"/"no" — training a regressor on it would fail on the first fold
    # with sklearn's own "could not convert string to float", not a message anyone
    # asked for. This is the mismatch a manually-overridden "what are you predicting"
    # answer can produce (#96's live testing: task=regression submitted against a
    # column that is not numeric).
    response = client.post(
        "/api/train",
        files={"file": ("binary-sales.csv", _binary_sales(), "text/csv")},
        data={"target": "sold", "task": "regression", "methods": ["decision_tree"]},
    )
    assert response.status_code == 422
    assert response.json()["detail"]["reason"] == "not-numeric-for-regression"


def test_polling_an_unknown_job_id_is_404():
    assert client.get("/api/train/no-such-job").status_code == 404


def test_stopping_an_unknown_job_id_is_404():
    assert client.post("/api/train/no-such-job/stop").status_code == 404


def test_stopping_an_already_finished_job_is_a_harmless_no_op():
    job_id = train(["linear_regression"]).json()["job_id"]
    wait_until_done(job_id)

    response = client.post(f"/api/train/{job_id}/stop")

    assert response.status_code == 200
    assert response.json()["done"] is True


def method_charts(
    job_id: str,
    method: str,
    target: str = "price",
    *,
    file_bytes: bytes | None = None,
    filename: str = "strong-signal-houses.csv",
    feature_x: str | None = None,
    feature_y: str | None = None,
):
    data = {"target": target}
    if feature_x is not None:
        data["feature_x"] = feature_x
    if feature_y is not None:
        data["feature_y"] = feature_y
    return client.post(
        f"/api/train/{job_id}/{method}/charts",
        files={"file": (filename, file_bytes or _strong_signal_houses(), "text/csv")},
        data=data,
    )


def _strong_signal_houses() -> bytes:
    from mlsandbox.config import PROJECT_ROOT

    return (PROJECT_ROOT / "examples" / "strong-signal-houses.csv").read_bytes()


def _binary_sales() -> bytes:
    from mlsandbox.config import PROJECT_ROOT

    return (PROJECT_ROOT / "examples" / "binary-sales.csv").read_bytes()


def test_linear_regression_charts_reuse_the_already_fitted_pipeline():
    job_id = train_file("strong-signal-houses.csv", ["linear_regression"]).json()["job_id"]
    wait_until_done(job_id)

    response = method_charts(job_id, "linear_regression")

    assert response.status_code == 200
    body = response.json()
    n_rows = len(_strong_signal_houses().decode().splitlines()) - 1
    assert len(body["residual"]["points"]) == n_rows
    assert len(body["predicted_vs_actual"]["points"]) == n_rows
    assert body["predicted_vs_actual"]["r2"] > 0.9
    assert len(body["leverage"]["points"]) == n_rows
    assert len(body["coefficients"]["bars"]) > 0


def test_linear_regression_demo_charts_have_a_real_high_leverage_point():
    # linear-regression-demo.csv plants two deliberately extreme rows specifically so
    # the leverage chart has something worth flagging, not a tight, uneventful cluster
    # (strong-signal-houses.csv's leverage all sits within 0.009-0.022).
    from mlsandbox.config import PROJECT_ROOT

    job_id = train_file(
        "linear-regression-demo.csv", ["linear_regression"], target="price"
    ).json()["job_id"]
    wait_until_done(job_id)

    response = method_charts(
        job_id,
        "linear_regression",
        target="price",
        file_bytes=(PROJECT_ROOT / "examples" / "linear-regression-demo.csv").read_bytes(),
        filename="linear-regression-demo.csv",
    )

    assert response.status_code == 200
    leverage = [p["leverage"] for p in response.json()["leverage"]["points"]]
    assert max(leverage) > 0.3


def test_logistic_regression_charts_reuse_the_already_fitted_pipeline():
    file_bytes = _binary_sales()
    job_id = train_file(
        "binary-sales.csv", ["logistic_regression"], target="sold", task="binary classification"
    ).json()["job_id"]
    wait_until_done(job_id)

    response = method_charts(
        job_id,
        "logistic_regression",
        target="sold",
        file_bytes=file_bytes,
        filename="binary-sales.csv",
    )

    assert response.status_code == 200
    body = response.json()
    assert body["roc"] is not None
    assert 0.0 <= body["roc"]["auc"] <= 1.0
    assert set(body["confusion_matrix"]["labels"]) == {"no", "yes"}
    assert len(body["coefficients"]["bars"]) == 2


def test_lda_charts_reuse_the_already_fitted_pipeline():
    file_bytes = _binary_sales()
    job_id = train_file(
        "binary-sales.csv", ["lda"], target="sold", task="binary classification"
    ).json()["job_id"]
    wait_until_done(job_id)

    response = method_charts(
        job_id, "lda", target="sold", file_bytes=file_bytes, filename="binary-sales.csv"
    )

    assert response.status_code == 200
    body = response.json()
    assert set(body["boundary"]["classes"]) == {"no", "yes"}
    assert body["boundary"]["too_many_classes"] is False
    assert len(body["boundary"]["grid"]) > 0
    assert set(body["confusion_matrix"]["labels"]) == {"no", "yes"}


def test_qda_boundary_honours_a_requested_feature_pair():
    file_bytes = _binary_sales()
    job_id = train_file(
        "binary-sales.csv", ["qda"], target="sold", task="binary classification"
    ).json()["job_id"]
    wait_until_done(job_id)

    response = method_charts(
        job_id,
        "qda",
        target="sold",
        file_bytes=file_bytes,
        filename="binary-sales.csv",
        feature_x="bedrooms",
        feature_y="size_m2",
    )

    assert response.status_code == 200
    body = response.json()
    assert body["boundary"]["feature_x"] == "bedrooms"
    assert body["boundary"]["feature_y"] == "size_m2"


def test_knn_charts_reuse_the_already_fitted_pipeline():
    file_bytes = _binary_sales()
    job_id = train_file(
        "binary-sales.csv", ["knn"], target="sold", task="binary classification"
    ).json()["job_id"]
    wait_until_done(job_id)

    response = method_charts(
        job_id, "knn", target="sold", file_bytes=file_bytes, filename="binary-sales.csv"
    )

    assert response.status_code == 200
    body = response.json()
    assert len(body["tuning"]["points"]) > 0
    assert body["tuning"]["chosen_k"] in [p["k"] for p in body["tuning"]["points"]]
    assert body["boundary"]["too_many_classes"] is False
    assert len(body["boundary"]["grid"]) > 0
    assert "confusion_matrix" not in body


def test_naive_bayes_charts_reuse_the_already_fitted_pipeline():
    file_bytes = _binary_sales()
    job_id = train_file(
        "binary-sales.csv", ["naive_bayes"], target="sold", task="binary classification"
    ).json()["job_id"]
    wait_until_done(job_id)

    response = method_charts(
        job_id, "naive_bayes", target="sold", file_bytes=file_bytes, filename="binary-sales.csv"
    )

    assert response.status_code == 200
    body = response.json()
    assert body["roc"] is not None
    assert 0.0 <= body["roc"]["auc"] <= 1.0
    assert set(body["confusion_matrix"]["labels"]) == {"no", "yes"}


def test_ridge_charts_reuse_the_already_fitted_pipeline():
    job_id = train_file("strong-signal-houses.csv", ["ridge"]).json()["job_id"]
    wait_until_done(job_id)

    response = method_charts(job_id, "ridge")

    assert response.status_code == 200
    body = response.json()
    assert len(body["shrinkage"]["points"]) > 0
    assert body["shrinkage"]["x_label"] == "α"
    assert len(body["shrinkage"]["promoted_features"]) > 0
    assert body["tuning"]["chosen_x"] in [p["x"] for p in body["tuning"]["points"]]


def test_lasso_charts_reuse_the_already_fitted_pipeline():
    file_bytes = _binary_sales()
    job_id = train_file(
        "binary-sales.csv", ["lasso"], target="sold", task="binary classification"
    ).json()["job_id"]
    wait_until_done(job_id)

    response = method_charts(
        job_id, "lasso", target="sold", file_bytes=file_bytes, filename="binary-sales.csv"
    )

    assert response.status_code == 200
    body = response.json()
    assert body["tuning"]["x_label"] == "C"
    assert len(body["shrinkage"]["points"]) > 0


def test_charts_for_a_method_with_no_panel_yet_is_422():
    job_id = train(["decision_tree"]).json()["job_id"]
    wait_until_done(job_id)

    response = method_charts(job_id, "decision_tree")

    assert response.status_code == 422
    assert response.json()["detail"]["reason"] == "no-charts-for-method"


def test_charts_for_a_method_that_never_finished_is_404():
    job_id = train(["linear_regression"]).json()["job_id"]
    # No wait_until_done: the method has not finished fitting yet.

    response = method_charts(job_id, "linear_regression")

    assert response.status_code == 404
    assert response.json()["detail"]["reason"] == "no-fitted-method"


def test_charts_for_an_unknown_job_id_is_404():
    response = method_charts("no-such-job", "linear_regression")
    assert response.status_code == 404
