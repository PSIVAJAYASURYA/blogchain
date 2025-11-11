from flask import Flask, request, jsonify, send_from_directory
import hashlib, json, time, requests, sys

app = Flask(__name__)

# ---------------- BLOCKCHAIN STRUCTURE ----------------
class Block:
    def __init__(self, index, timestamp, data, previous_hash):
        self.index = index
        self.timestamp = timestamp
        self.data = data
        self.previous_hash = previous_hash
        self.hash = self.calculate_hash()

    def calculate_hash(self):
        block_string = f"{self.index}{self.timestamp}{self.data}{self.previous_hash}"
        return hashlib.sha256(block_string.encode()).hexdigest()

class Blockchain:
    def __init__(self):
        self.chain = [self.create_genesis_block()]
        self.peers = set()

    def create_genesis_block(self):
        return Block(0, time.time(), "Genesis Block", "0")

    def get_last_block(self):
        return self.chain[-1]

    def add_block(self, data):
        last_block = self.get_last_block()
        new_block = Block(len(self.chain), time.time(), data, last_block.hash)
        self.chain.append(new_block)
        return new_block

    def add_peer(self, node):
        self.peers.add(node)

    def receive_block(self, block_data):
        block = Block(block_data["index"], block_data["timestamp"],
                      block_data["data"], block_data["previous_hash"])
        if block.hash == block_data["hash"]:
            self.chain.append(block)
            return True
        return False

blockchain = Blockchain()

# ---------------- API ROUTES ----------------

@app.route("/")
def serve_ui():
    return send_from_directory(".", "chat.html")

@app.route("/add_block", methods=["POST"])
def add_block():
    data = request.get_json().get("data")
    new_block = blockchain.add_block(data)
    broadcast_block(new_block)
    return jsonify({"message": "Block added", "hash": new_block.hash}), 200

@app.route("/receive_block", methods=["POST"])
def receive_block():
    block_data = request.get_json()
    added = blockchain.receive_block(block_data)
    return jsonify({"message": "Block received", "added": added}), 200

@app.route("/chain", methods=["GET"])
def get_chain():
    chain_data = [{
        "index": block.index,
        "timestamp": block.timestamp,
        "data": block.data,
        "previous_hash": block.previous_hash,
        "hash": block.hash
    } for block in blockchain.chain]
    return jsonify(chain_data), 200

@app.route("/register_peer", methods=["POST"])
def register_peer():
    node = request.get_json().get("node")
    if not node:
        return jsonify({"error": "No node provided"}), 400

    blockchain.add_peer(node)

    # 🔁 Auto-register back on peer node
    try:
        requests.post(f"{node}/register_peer",
                      json={"node": f"http://127.0.0.1:{request.host.split(':')[1]}"})
    except:
        pass

    return jsonify({"message": f"Node {node} added and auto-registered back"}), 200

# ---------------- BROADCAST ----------------

def broadcast_block(block):
    for peer in blockchain.peers:
        try:
            requests.post(f"{peer}/receive_block", json={
                "index": block.index,
                "timestamp": block.timestamp,
                "data": block.data,
                "previous_hash": block.previous_hash,
                "hash": block.hash
            })
        except:
            pass

# ---------------- MAIN ----------------

if __name__ == "__main__":
    port = 5000
    username = "Santhosh"  # default
    if len(sys.argv) > 1:
        port = int(sys.argv[1])
    if port == 5001:
        username = "Siva"

    # Store username in Flask config for UI
    app.config["USERNAME"] = username
    print(f"Running as {username} on port {port}")
    app.run(host="127.0.0.1", port=port)
