import psutil
import time
import threading
import requests
import logging
from flask import Flask, redirect, render_template

# Setup logging configuration
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

ALL_SERVERS = [
    'http://localhost:5001',
    'http://localhost:5002',
    'http://localhost:5003'
]

active_servers = list(ALL_SERVERS)
current = 0

# Initialize metrics storage
server_stats = {server: {'requests': 0, 'avg_response_time': 0} for server in ALL_SERVERS}

# Health checker thread
def health_check():
    global active_servers, server_stats
    while True:
        healthy = []
        for server in ALL_SERVERS:
            try:
                r = requests.get(server + "/health", timeout=2)
                if r.status_code == 200:
                    healthy.append(server)
                    # Track response time
                    response_time = r.elapsed.total_seconds()
                    stats = server_stats[server]
                    stats['requests'] += 1
                    stats['avg_response_time'] = (stats['avg_response_time'] * (stats['requests'] - 1) + response_time) / stats['requests']
            except:
                pass
        
        # Update active servers and log the changes
        if healthy != active_servers:
            logger.info(f"Active servers changed: {healthy}")
        active_servers = healthy
        logger.info(f"Active servers: {active_servers}")
        logger.info(f"Server stats: {server_stats}")
        time.sleep(5)

# Start health check in a separate thread
threading.Thread(target=health_check, daemon=True).start()

@app.route('/')
def load_balance():
    global current
    if not active_servers:
        logger.error("All servers are down!")
        return "All servers are down", 503
    server = active_servers[current % len(active_servers)]
    current += 1
    server_stats[server]['requests'] += 1  # Increment request count
    logger.info(f"Redirecting to server: {server}")
    return redirect(server)

# Route to show server stats
@app.route('/status')
def status():
    return render_template('status.html', server_stats=server_stats)

if __name__ == '__main__':
    app.run(port=8080)
