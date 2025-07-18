from flask import Flask, request, jsonify
from flask_cors import CORS
import time

app = Flask(__name__)
CORS(app)

# Store all devices
devices = {}
DEVICE_TIMEOUT = 20  # seconds
REQUEST_TIMEOUT = 30  # seconds

@app.route("/")
def home():
    return "✅ MMW Remote API is running"

@app.route("/register", methods=["POST"])
def register():
    data = request.get_json()
    device_id = data.get("id")
    ip = data.get("ip")
    name = data.get("name", device_id)

    if not device_id or not ip:
        return jsonify({"error": "Missing ID or IP"}), 400

    devices[device_id] = {
        "ip": ip,
        "name": name,
        "status": "available",
        "last_seen": time.time(),
        "requested_by": None,
        "request_time": None
    }
    return jsonify({"success": True})

@app.route("/heartbeat", methods=["POST"])
def heartbeat():
    data = request.get_json()
    device_id = data.get("id")
    if device_id in devices:
        devices[device_id]["last_seen"] = time.time()
        return jsonify({"success": True})
    return jsonify({"error": "Device not found"}), 404

@app.route("/list", methods=["GET"])
def list_devices():
    now = time.time()
    active = []
    stale = []

    for device_id, info in devices.items():
        if now - info["last_seen"] <= DEVICE_TIMEOUT:
            active.append({
                "id": device_id,
                "name": info["name"],
                "status": info["status"],
                "ip": info["ip"]
            })
        else:
            stale.append(device_id)

    for device_id in stale:
        del devices[device_id]

    return jsonify(active)

@app.route("/request", methods=["POST"])
def send_request():
    data = request.get_json()
    receiver_id = data.get("receiver")  # Sender's device ID
    requester_id = data.get("id")       # Receiver's device ID

    if receiver_id not in devices:
        return jsonify({"error": "Receiver not found"}), 404

    devices[receiver_id]["status"] = "requested"
    devices[receiver_id]["requested_by"] = requester_id
    devices[receiver_id]["request_time"] = time.time()
    return jsonify({"success": True})

@app.route("/respond", methods=["POST"])
def respond():
    data = request.get_json()
    device_id = data.get("id")
    accept = data.get("accept", False)

    if device_id not in devices:
        return jsonify({"error": "Device not found"}), 404

    if accept:
        devices[device_id]["status"] = "accepted"
    else:
        devices[device_id]["status"] = "available"
        devices[device_id]["requested_by"] = None

    devices[device_id]["request_time"] = None
    return jsonify({"success": True})

@app.route("/status/<device_id>", methods=["GET"])
def check_status(device_id):
    now = time.time()

    if device_id not in devices:
        return jsonify({"status": "not_found"}), 404

    info = devices[device_id]

    # Timeout if pending too long
    if info["status"] == "requested" and info["request_time"]:
        if now - info["request_time"] > REQUEST_TIMEOUT:
            info["status"] = "available"
            info["requested_by"] = None
            info["request_time"] = None

    # Case 1: Sender checking
    if info["status"] == "requested":
        return jsonify({
            "status": "requested",
            "requested_by": info["requested_by"]
        })

    # Case 2: Receiver checking if request accepted
    if info["status"] == "accepted":
        return jsonify({
            "status": "accepted",
            "ip": info["ip"]
        })

    return jsonify({"status": info["status"]})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
