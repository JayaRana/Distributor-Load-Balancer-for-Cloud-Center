import os
import requests
import subprocess
import datetime
import random
import time
from collections import defaultdict
from flask import Flask, request, render_template, redirect, jsonify

app = Flask(__name__)

HAPROXY_BASE_CFG = "/mnt/e/cloud-load-balancer/base.cfg"
HAPROXY_ACTIVE_CFG = "/etc/haproxy/haproxy.cfg"

STRATEGIES = {
    "roundrobin": "backend roundrobin_servers",
    "leastconn": "backend leastconn_servers",
    "source": "backend source_servers"
}

# Request log simulation for traffic chart
request_log = defaultdict(int)

# Performance log: track requests, total response time, and errors
performance_log = {
    "server1": {"requests": 0, "total_response_time": 0.0, "errors": 0},
    "server2": {"requests": 0, "total_response_time": 0.0, "errors": 0}
}

@app.route("/", methods=["GET", "POST"])
def control():
    if request.method == "POST":
        backend = request.form.get("backend")
        if backend in STRATEGIES:
            update_haproxy_config(backend)
        return redirect("/")

    # ✅ FIX: Prepare request_counts for Chart.js bar chart in index.html
    request_counts = [
        request_log["server1"],  # Server 1
        request_log["server2"],  # Server 2
        0,                       # Server 3 placeholder
        0,                       # Server 4 placeholder
        0                        # Server 5 placeholder
    ]

    return render_template("index.html", request_counts=request_counts)

@app.route("/simulate/<server>")
def simulate_request(server):
    if server in ["server1", "server2"]:
        response_time = random.uniform(0.05, 0.3)
        time.sleep(response_time)  # simulate latency
        is_error = random.random() < 0.1

        request_log[server] += 1
        performance_log[server]["requests"] += 1
        performance_log[server]["total_response_time"] += response_time
        if is_error:
            performance_log[server]["errors"] += 1

        status = "error" if is_error else "success"
        return f"Simulated request to {server} with {status}, took {response_time*1000:.1f} ms"
    return "Invalid server"

@app.route("/api/traffic")
def get_traffic_data():
    now = datetime.datetime.now().strftime("%H:%M:%S")
    return jsonify({
        "labels": [now],
        "datasets": [
            {
                "label": "Server 1",
                "data": [request_log["server1"]],
                "borderColor": "rgba(75, 192, 192, 1)",
                "backgroundColor": "rgba(75, 192, 192, 0.2)",
                "fill": True,
            },
            {
                "label": "Server 2",
                "data": [request_log["server2"]],
                "borderColor": "rgba(255, 99, 132, 1)",
                "backgroundColor": "rgba(255, 99, 132, 0.2)",
                "fill": True,
            }
        ]
    })

@app.route("/stats")
def stats():
    log_files = {
        "Server 1": "/mnt/e/cloud-load-balancer/server1.log",
        "Server 2": "/mnt/e/cloud-load-balancer/server2.log"
    }
    stats = {}
    for name, path in log_files.items():
        if os.path.exists(path):
            with open(path, "r") as f:
                lines = f.readlines()
            stats[name] = len(lines)
        else:
            stats[name] = 0
    return jsonify(stats)

@app.route("/api/health")
def health_check():
    statuses = {}
    servers = {
        "Server 1": "http://127.0.0.1:5001",
        "Server 2": "http://127.0.0.1:5002"
    }
    for name, url in servers.items():
        try:
            res = requests.get(url, timeout=1)
            statuses[name] = (res.status_code == 200)
        except Exception:
            statuses[name] = False
    return jsonify(statuses)

@app.route("/api/performance")
def performance():
    data = {}
    for server in ["server1", "server2"]:
        stats = performance_log[server]
        total_req = stats["requests"]
        avg_resp = (stats["total_response_time"] / total_req) if total_req > 0 else 0
        error_rate = (stats["errors"] / total_req) if total_req > 0 else 0
        data[server] = {
            "total_requests": total_req,
            "average_response_time_ms": round(avg_resp * 1000, 2),
            "error_rate_percent": round(error_rate * 100, 2)
        }
    return jsonify(data)

def update_haproxy_config(strategy):
    with open(HAPROXY_BASE_CFG, "r") as base:
        content = base.read()

    with open("/mnt/e/cloud-load-balancer/backends.cfg", "r") as backends:
        backend_sections = backends.read().split("###")

    selected_backend = next((b for b in backend_sections if strategy in b), "")
    full_config = content + "\n" + selected_backend

    with open(HAPROXY_ACTIVE_CFG, "w") as out:
        out.write(full_config)

    subprocess.run(["sudo", "systemctl", "reload", "haproxy"])

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
