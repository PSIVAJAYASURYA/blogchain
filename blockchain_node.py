from flask import Flask, request, jsonify
import hashlib, json, time, requests

app = Flask(__name__)

# ---- BLOCKCHAIN CLASS ----
class Block:
    def __init__(self, index, timestamp, data, previous_hash=''):
        self.index = index
        self.timestamp = timestamp
        self.data = data
        self.previous_hash = previous_hash
        self.hash = self.calculate_hash()

    def calculate_hash(self):
        content = f"{self.index}{self.timestamp}{self.data}{self.previous_hash}"
        return hashlib.sha256(content.encode()).hexdigest()


class Blockchain:
    def __init__(self):
        self.chain = [self.create_genesis_block()]
        self.peers = set()

    def create_genesis_block(self):
        return Block(0, time.time(), "Genesis Block", "0")

    def get_latest_block(self):
        return self.chain[-1]

    def add_block(self, new_data):
        prev_block = self.get_latest_block()
        new_block = Block(len(self.chain), time.time(), new_data, prev_block.hash)
        self.chain.append(new_block)
        return new_block

    def is_chain_valid(self):
        for i in range(1, len(self.chain)):
            cur = self.chain[i]
            prev = self.chain[i - 1]
            if cur.hash != cur.calculate_hash() or cur.previous_hash != prev.hash:
                return False
        return True


# ---- SETUP ----
blockchain = Blockchain()


# ---- FLASK ROUTES ----
@app.route('/chain', methods=['GET'])
def get_chain():
    chain_data = [b.__dict__ for b in blockchain.chain]
    return jsonify(chain_data), 200


@app.route('/add_block', methods=['POST'])
def add_block():
    data = request.json.get('data')
    new_block = blockchain.add_block(data)
    # Broadcast to peers
    broadcast_block(new_block)
    return jsonify(new_block.__dict__), 201


@app.route('/register_peer', methods=['POST'])
def register_peer():
    node_address = request.json.get('node')
    if node_address:
        blockchain.peers.add(node_address)
        return jsonify({'message': f'Node {node_address} added successfully'}), 201
    return jsonify({'error': 'Invalid node address'}), 400


@app.route('/receive_block', methods=['POST'])
def receive_block():
    block_data = request.json
    block = Block(**block_data)
    last_hash = blockchain.get_latest_block().hash
    if block.previous_hash == last_hash:
        blockchain.chain.append(block)
        return jsonify({'message': 'Block accepted'}), 200
    return jsonify({'message': 'Block rejected'}), 400


def broadcast_block(block):
    for peer in blockchain.peers:
        try:
            requests.post(f"{peer}/receive_block", json=block.__dict__)
        except:
            pass


if __name__ == '__main__':
    app.run(port=5001)
