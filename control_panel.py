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

# Request log simulation for traffic chart (for all 5 servers)
request_log = defaultdict(int)

# Performance log: track requests, response time, errors (all 5 servers)
performance_log = {
    f"server{i}": {"requests": 0, "total_response_time": 0.0, "errors": 0} for i in range(1,6)
}

@app.route("/", methods=["GET", "POST"])
def control():
    if request.method == "POST":
        backend = request.form.get("backend")
        if backend in STRATEGIES:
            update_haproxy_config(backend)
        return redirect("/")

    # Provide request counts for all 5 servers (for frontend charts)
    request_counts = [request_log[f"server{i}"] for i in range(1, 6)]

    return render_template("index.html", request_counts=request_counts)

@app.route("/simulate/<server>")
def simulate_request(server):
    # Simulate request for any server from server1 to server5
    if server in performance_log:
        response_time = random.uniform(0.05, 0.3)
        time.sleep(response_time)  # simulate latency

        # Simulate 10% error rate for all servers except server4 (flaky) and server5 (random fail)
        error_rate = 0.1

        # Customize error rates for flaky and random fail servers
        if server == "server4":
            # Higher delay and maybe more error chance
            response_time = random.uniform(0.5, 2.0)
            time.sleep(response_time)
            error_rate = 0.2
        elif server == "server5":
            # 30% chance to fail (align with your flask server5.py)
            error_rate = 0.3

        is_error = random.random() < error_rate

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
    labels = [now]
    datasets = []
    colors = [
        "rgba(75, 192, 192, 1)",  # Server 1
        "rgba(255, 99, 132, 1)",  # Server 2
        "rgba(255, 206, 86, 1)",  # Server 3
        "rgba(54, 162, 235, 1)",  # Server 4
        "rgba(153, 102, 255, 1)"  # Server 5
    ]

    for i in range(1, 6):
        server = f"server{i}"
        datasets.append({
            "label": f"Server {i}",
            "data": [request_log[server]],
            "borderColor": colors[i-1],
            "backgroundColor": colors[i-1].replace('1)', '0.2)'),
            "fill": True,
        })

    return jsonify({
        "labels": labels,
        "datasets": datasets
    })

@app.route("/stats")
def stats():
    log_files = {
        "Server 1": "/mnt/e/cloud-load-balancer/server1.log",
        "Server 2": "/mnt/e/cloud-load-balancer/server2.log",
        "Server 3": "/mnt/e/cloud-load-balancer/server3.log",
        "Server 4": "/mnt/e/cloud-load-balancer/server4.log",
        "Server 5": "/mnt/e/cloud-load-balancer/server5.log"
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
        "Server 1": "http://127.0.0.1:5001/health",
        "Server 2": "http://127.0.0.1:5002/health",
        "Server 3": "http://127.0.0.1:5003/health",
        "Server 4": "http://127.0.0.1:5004/health",
        "Server 5": "http://127.0.0.1:5005/health"
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
    for i in range(1, 6):
        server = f"server{i}"
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
    # Read base haproxy config
    with open(HAPROXY_BASE_CFG, "r") as base:
        content = base.read()

    # Read backend configs
    with open("/mnt/e/cloud-load-balancer/backends.cfg", "r") as backends:
        backend_sections = backends.read().split("###")

    # Find selected backend by strategy name
    selected_backend = next((b for b in backend_sections if strategy in b), "")
    full_config = content + "\n" + selected_backend

    # Write to active haproxy config
    with open(HAPROXY_ACTIVE_CFG, "w") as out:
        out.write(full_config)

    # Reload haproxy to apply changes
    subprocess.run(["sudo", "systemctl", "reload", "haproxy"])

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
