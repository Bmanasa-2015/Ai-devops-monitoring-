from flask import Flask, jsonify
import socket
import time

app = Flask(__name__)

@app.route("/")
def home():
    return jsonify({
        "application": "AI DevOps Monitoring Application",
        "status": "running",
        "hostname": socket.gethostname()
    })

@app.route("/health")
def health():
    return jsonify({
        "status": "healthy"
    })

@app.route("/api/info")
def info():
    return jsonify({
        "application": "AI DevOps Monitoring Application",
        "version": "1.0",
        "environment": "development",
        "timestamp": time.time()
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)