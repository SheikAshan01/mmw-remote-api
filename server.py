from flask import Flask, request, jsonify
from datetime import datetime, timedelta

app = Flask(__name__)

# In-memory storage
online_users = {}  # key = sender_id, value = {ip, name, last_seen, status, requested_by}
REQUEST_TIMEOUT = timedelta(seconds=30)

@app.route("/")
def home():
    return "MMW Remote API is running"

@app.route("/register", methods=["POST"])
def register():
    data = request.json
    sender_id = data.get("id")
    ip = data.get("ip")
    name = data.get("name")
    if not sender_id or not ip:
        return {"error": "Missing id or ip"}, 400

    online_users[sender_id] = {
        "ip": ip,
        "name": name or sender_id,
        "last_seen": datetime.now(),
        "status": "available",
        "requested_by": None
    }
    return {"status": "registered"}

@app.route("/list", methods=["GET"])
def list_users():
    now = datetime.now()
    result = []
    for uid, info in online_users.items():
        if now - info["last_seen"] < timedelta(seconds=60):
            result.append({
                "id": uid,
                "name": info["name"],
                "ip": info["ip"],
                "status": info["status"]
            })
    return jsonify(result)

@app.route("/request", methods=["POST"])
def request_connection():
    data = request.json
    sender_id = data.get("id")
    receiver_id = data.get("receiver")

    sender = online_users.get(sender_id)
    if not sender:
        return {"error": "Sender not found"}, 404

    sender["status"] = "requested"
    sender["requested_by"] = receiver_id
    return {"status": "request_sent"}

@app.route("/status/<sender_id>", methods=["GET"])
def check_status(sender_id):
    user = online_users.get(sender_id)
    if not user:
        return {"error": "User not found"}, 404

    return {
        "status": user["status"],
        "requested_by": user["requested_by"]
    }

@app.route("/respond", methods=["POST"])
def respond():
    data = request.json
    sender_id = data.get("id")
    accepted = data.get("accept")

    user = online_users.get(sender_id)
    if not user:
        return {"error": "User not found"}, 404

    if accepted:
        user["status"] = "accepted"
    else:
        user["status"] = "available"
        user["requested_by"] = None

    return {"status": "response_recorded"}

@app.route("/heartbeat", methods=["POST"])
def heartbeat():
    data = request.json
    sender_id = data.get("id")
    if sender_id in online_users:
        online_users[sender_id]["last_seen"] = datetime.now()
    return {"status": "heartbeat_received"}
