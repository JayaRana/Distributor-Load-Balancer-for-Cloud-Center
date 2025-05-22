import json
from datetime import datetime
import threading

LOG_FILE = "traffic_logs.jsonl"
lock = threading.Lock()  # To avoid race conditions if multithreaded

def log_request(strategy: str, server_name: str):
    """
    Log a request event with strategy and server used.
    Each log entry is a JSON object saved as a line in a file.
    """
    log_entry = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "strategy": strategy,
        "server": server_name
    }

    # Write the log entry atomically to avoid conflicts
    with lock:
        with open(LOG_FILE, "a") as f:
            f.write(json.dumps(log_entry) + "\n")

def read_logs():
    """
    Read all logged request entries.
    Returns a list of dicts.
    """
    logs = []
    try:
        with open(LOG_FILE, "r") as f:
            for line in f:
                logs.append(json.loads(line))
    except FileNotFoundError:
        # No logs yet
        pass
    return logs


# For quick local testing
if __name__ == "__main__":
    log_request("roundrobin", "server1")
    log_request("leastconn", "server3")
    all_logs = read_logs()
    print(f"Total logs: {len(all_logs)}")
    print(all_logs[-2:])
