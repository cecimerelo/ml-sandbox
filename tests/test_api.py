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


def test_skipped_columns_are_named_in_the_response():
    notes = "\n".join(f"note {i},{i},{i}" for i in range(10))
    response = upload_csv(f"notes,x,y\n{notes}\n".encode())
    assert response.json()["skipped"] == ["notes"]


def test_a_missing_file_is_rejected_by_the_framework():
    assert client.post("/api/dataset").status_code == 422
