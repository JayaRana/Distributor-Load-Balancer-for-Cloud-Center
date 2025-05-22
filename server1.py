from flask import Flask, request
from datetime import datetime

app = Flask(__name__)

@app.route('/')
def index():
    with open("server1.log", "a") as log:  
        log.write(f"{datetime.now()} - Request from {request.remote_addr}\n")
    return 'Response from Server 1'

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)
