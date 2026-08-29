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
