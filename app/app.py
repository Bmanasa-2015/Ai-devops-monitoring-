
from flask import Flask, jsonify, request, Response, g
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
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


@app.before_request
def start_timer():
    g.request_start_time = time.perf_counter()


@app.after_request
def record_metrics(response):
    # Do not count Prometheus scrapes as application traffic.
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


@app.route("/metrics")
def metrics():
    return Response(
        generate_latest(),
        content_type=CONTENT_TYPE_LATEST,
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
