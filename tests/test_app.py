import os
import sys

sys.path.insert(
    0,
    os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "app")
    ),
)

from app import app as flask_app


def test_home():
    response = flask_app.test_client().get("/")
    assert response.status_code == 200
    assert response.json["status"] == "running"


def test_health():
    response = flask_app.test_client().get("/health")
    assert response.status_code == 200
    assert response.json["status"] == "healthy"


def test_info():
    response = flask_app.test_client().get("/api/info")
    assert response.status_code == 200
    assert response.json["version"] == "1.0"


def test_prometheus_metrics():
    response = flask_app.test_client().get("/metrics")
    assert response.status_code == 200
    assert b"python_gc_objects_collected_total" in response.data