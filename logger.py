import requests
import csv
import os
from datetime import datetime
from pathlib import Path

API_BASE_URL = "http://localhost:8080/api"
LOG_DIR = "csv_logs"

Path(LOG_DIR).mkdir(exist_ok=True)

def init_csv_file(filename, headers):
    filepath = os.path.join(LOG_DIR, filename)
    if not os.path.exists(filepath):
        with open(filepath, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(headers)

def log_csv(filename, row):
    filepath = os.path.join(LOG_DIR, filename)
    with open(filepath, 'a', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(row)

def fetch(endpoint):
    try:
        res = requests.get(f"{API_BASE_URL}/{endpoint}", timeout=3)
        res.raise_for_status()
        return res.json()
    except requests.RequestException:
        return {}

def setup_logging():
    init_csv_file("traffic.csv", ["Timestamp", "Server1", "Server2"])
    init_csv_file("health.csv", ["Timestamp", "Server 1", "Server 2"])
    init_csv_file("performance.csv", ["Timestamp", "Server", "Total Requests", "Avg Resp Time (ms)", "Error Rate (%)"])

def log_all_data():
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    traffic = fetch("traffic")
    if "datasets" in traffic:
        s1 = traffic["datasets"][0]["data"][0]
        s2 = traffic["datasets"][1]["data"][0]
        log_csv("traffic.csv", [timestamp, s1, s2])

    health = fetch("health")
    if health:
        log_csv("health.csv", [timestamp, health.get("Server 1", "N/A"), health.get("Server 2", "N/A")])

    perf = fetch("performance")
    if perf:
        for server, stats in perf.items():
            log_csv("performance.csv", [
                timestamp, server, stats["total_requests"],
                stats["average_response_time_ms"], stats["error_rate_percent"]
            ])
