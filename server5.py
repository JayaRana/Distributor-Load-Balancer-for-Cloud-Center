from flask import Flask, request
from datetime import datetime
import random

app = Flask(__name__)

@app.route('/')
def index():
    if random.random() < 0.3:  # 30% chance to simulate failure
        return 'Server 5 is temporarily down', 503
    with open("server5.log", "a") as log:
        log.write(f"{datetime.now()} - Request from {request.remote_addr}\n")
    return 'Response from Server 5 (Sometimes Down)'

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5005)
