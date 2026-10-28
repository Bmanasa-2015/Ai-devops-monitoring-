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

def test_ai_detects_extreme_value():
    client = flask_app.test_client()
    response = client.post(
        "/api/anomaly/detect",
        json={"values": [10, 11, 9, 10, 12, 11, 10, 9, 10, 1000]},
    )

    assert response.status_code == 200
    data = response.get_json()
    assert data["algorithm"] == "IsolationForest"
    assert data["anomaly_count"] >= 1

    anomalies = [
        item for item in data["results"]
        if item["status"] == "anomaly"
    ]
    assert any(item["value"] == 1000.0 for item in anomalies)


def test_ai_rejects_too_few_values():
    client = flask_app.test_client()
    response = client.post(
        "/api/anomaly/detect",
        json={"values": [10, 11, 12]},
    )

    assert response.status_code == 400
