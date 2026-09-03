"""The HTTP surface.

Thin for now — the health endpoint and the property that makes it worth having.
"""

from fastapi.testclient import TestClient

from mlsandbox.api import app
from mlsandbox.methods import METHODS

client = TestClient(app)


def test_health_reports_ok():
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_health_proves_the_server_can_reach_the_study():
    """Not merely that the process is up.

    The whole design rests on the application calling the same code the study measured. A
    health check that passes while the engine is unimportable hides exactly that failure.
    """
    assert client.get("/api/health").json()["methods"] == len(METHODS)


def test_an_unknown_route_is_a_404_not_a_crash():
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


def test_the_three_explainability_levels_give_three_answers():
    """A control whose middle option changes nothing is worse than not asking (D-042)."""
    answers = {
        level: ask(explainability=level).json()["recommended"]["method"]
        for level in ("not important", "somewhat", "critical")
    }
    assert len(set(answers.values())) == 3


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


def test_a_thinly_supported_answer_is_reported_as_such():
    body = ask(missing="a lot").json()
    assert body["support"]["field"] == "missing"
    assert body["support"]["datasets"] < body["support"]["total"] / 10


def test_the_response_says_when_the_model_is_provisional():
    """A model trained on part of the collection is useful to build against and must never
    be mistaken for the finished one."""
    assert "provisional" in ask().json()
