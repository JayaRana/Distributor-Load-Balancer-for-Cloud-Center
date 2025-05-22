from flask import Flask, request
from datetime import datetime
import random
import time

app = Flask(__name__)

@app.route('/')
def index():
    delay = random.uniform(0.5, 2.0)  # Random delay between 0.5s and 2s
    time.sleep(delay)
    with open("server4.log", "a") as log:
        log.write(f"{datetime.now()} - Request from {request.remote_addr} - Delay: {delay:.2f}s\n")
    return 'Response from Server 4 (Flaky)'

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5004)
