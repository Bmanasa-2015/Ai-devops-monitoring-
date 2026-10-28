from flask import Flask, jsonify, request, Response, g
from flask import Flask, jsonify, request, Response, g
from prometheus_client import (
    Counter,
    Histogram,
    generate_latest,
    CONTENT_TYPE_LATEST,
)
from sklearn.ensemble import IsolationForest
import math
import socket
import time

app = Flask(__name__)

REQUEST_COUNT = Counter(
    "app_http_requests_total",
    "Total HTTP requests handled by the application",
    ["method", "endpoint", "status"],
)

REQUEST_LATENCY = Histogram(
    "app_http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "endpoint"],
)

AI_ANOMALY_OBSERVATIONS = Counter(
    "app_ai_anomaly_observations_total",
    "Number of anomalous observations detected by the model",
)


@app.before_request
def start_timer():
    g.request_start_time = time.perf_counter()


@app.after_request
def record_metrics(response):
    if request.path != "/metrics":
        endpoint = request.url_rule.rule if request.url_rule else "unmatched"

        REQUEST_COUNT.labels(
            request.method, endpoint, str(response.status_code)
        ).inc()

        start = getattr(g, "request_start_time", None)
        if start is not None:
            REQUEST_LATENCY.labels(
                request.method, endpoint
            ).observe(time.perf_counter() - start)

    return response


@app.route("/")
def home():
    return jsonify({
        "application": "AI DevOps Monitoring Application",
        "status": "running",
        "hostname": socket.gethostname(),
    })


@app.route("/health")
def health():
    return jsonify({"status": "healthy"}), 200


@app.route("/api/info")
def info():
    return jsonify({
        "application": "AI DevOps Monitoring Application",
        "version": "1.0",
        "environment": "development",
        "timestamp": time.time(),
    })


@app.route("/api/anomaly/detect", methods=["POST"])
def detect_anomalies():
    payload = request.get_json(silent=True)

    if not isinstance(payload, dict):
        return jsonify({"error": "A JSON object is required"}), 400

    values = payload.get("values")

    if (
        not isinstance(values, list)
        or not 8 <= len(values) <= 1000
    ):
        return jsonify({
            "error": "Provide between 8 and 1000 numeric values"
        }), 400

    if any(
        isinstance(value, bool)
        or not isinstance(value, (int, float))
        or not math.isfinite(value)
        for value in values
    ):
        return jsonify({
            "error": "All values must be finite numbers"
        }), 400

    features = [[float(value)] for value in values]

    model = IsolationForest(
        n_estimators=100,
        contamination=0.1,
        random_state=42,
    )

    labels = model.fit_predict(features)
    scores = model.decision_function(features)

    results = [
        {
            "index": index,
            "value": float(value),
            "status": "anomaly" if labels[index] == -1 else "normal",
            "anomaly_score": round(float(scores[index]), 6),
        }
        for index, value in enumerate(values)
    ]

    anomaly_count = sum(1 for label in labels if label == -1)

    if anomaly_count:
        AI_ANOMALY_OBSERVATIONS.inc(anomaly_count)

    return jsonify({
        "algorithm": "IsolationForest",
        "observations": len(values),
        "anomaly_count": anomaly_count,
        "results": results,
    })


@app.route("/metrics")
def metrics():
    return Response(
        generate_latest(),
        content_type=CONTENT_TYPE_LATEST,
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)