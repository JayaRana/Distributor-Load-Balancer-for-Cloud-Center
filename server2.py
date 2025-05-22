from flask import Flask, request
from datetime import datetime

app = Flask(__name__)

@app.route('/')
def index():
    with open("server2.log", "a") as log:  # ✅ Fixed here
        log.write(f"{datetime.now()} - Request from {request.remote_addr}\n")
    return 'Response from Server 2'

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5002)
