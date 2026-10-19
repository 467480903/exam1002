import math
import os

import requests
from flask import Flask, jsonify, request

from ledger import Ledger


NODE_ID = os.environ.get("NODE_ID", "node1")
PEERS = [peer for peer in os.environ.get("PEERS", "").split(",") if peer]
ALL_NODES = int(os.environ.get("ALL_NODES", "3"))
QUORUM = math.floor(ALL_NODES / 2) + 1
BYZANTINE = os.environ.get("BYZANTINE", "false").lower() == "true"
ledger = Ledger(os.environ.get("DB_PATH", "/data/ledger.db"))
app = Flask(__name__)


@app.get("/health")
def health():
    return jsonify({"node": NODE_ID, "height": ledger.height(), "byzantine": BYZANTINE})


@app.get("/state")
def state():
    balances, nonces = ledger.state()
    chain_valid, chain_reason = ledger.verify_chain()
    return jsonify({
        "node": NODE_ID,
        "height": ledger.height(),
        "tip": ledger.tip_hash(),
        "balances": balances,
        "nonces": nonces,
        "storage": {"engine": "SQLite", "path": ledger.path, "local_copy": True},
        "chain_integrity": {"valid": chain_valid, "reason": chain_reason},
    })


@app.get("/features")
def features():
    """返回本教学节点所展示的四类区块链机制。"""
    return jsonify({
        "node": NODE_ID,
        "cryptography": {
            "transaction_signature": "Ed25519",
            "block_hash": "SHA-256",
            "hash_linked_blocks": True,
        },
        "smart_contract": {
            "name": "PaymentContract",
            "rules": ["联盟成员", "数字签名", "正整数金额", "余额", "连续nonce"],
        },
        "consensus": {
            "type": "教学用多数表决",
            "nodes": ALL_NODES,
            "quorum": QUORUM,
            "byzantine": BYZANTINE,
        },
        "distributed_storage": {
            "engine": "SQLite",
            "path": ledger.path,
            "replicas": ALL_NODES,
        },
    })


@app.get("/chain")
def chain():
    return jsonify(ledger.blocks())


@app.post("/vote")
def vote():
    tx = request.get_json(force=True)["transaction"]
    valid, reason = ledger.validate_tx(tx)
    if BYZANTINE:
        return jsonify({"node": NODE_ID, "approve": False, "reason": "模拟拜占庭节点故意反对"})
    return jsonify({"node": NODE_ID, "approve": valid, "reason": reason})


@app.post("/commit")
def commit():
    block = request.get_json(force=True)["block"]
    valid, reason = ledger.validate_block(block, QUORUM)
    if not valid:
        return jsonify({"committed": False, "reason": reason}), 409
    ledger.append(block)
    return jsonify({"committed": True, "node": NODE_ID, "height": ledger.height()})


@app.post("/transactions")
def submit_transaction():
    tx = request.get_json(force=True)
    valid, reason = ledger.validate_tx(tx)
    if not valid:
        return jsonify({"committed": False, "reason": reason}), 400

    votes = [NODE_ID]
    vote_log = [{"node": NODE_ID, "approve": True, "reason": reason}]
    for peer in PEERS:
        try:
            result = requests.post(f"{peer}/vote", json={"transaction": tx}, timeout=3).json()
            vote_log.append(result)
            if result.get("approve"):
                votes.append(result["node"])
        except requests.RequestException as exc:
            vote_log.append({"node": peer, "approve": False, "reason": str(exc)})

    if len(votes) < QUORUM:
        return jsonify({"committed": False, "reason": "未达到多数共识", "votes": vote_log}), 409

    block = ledger.make_block(tx, NODE_ID, votes)
    ledger.append(block)
    commits = [{"node": NODE_ID, "committed": True}]
    for peer in PEERS:
        try:
            response = requests.post(f"{peer}/commit", json={"block": block}, timeout=3)
            commits.append(response.json())
        except requests.RequestException as exc:
            commits.append({"node": peer, "committed": False, "reason": str(exc)})
    return jsonify({"committed": True, "block": block, "votes": vote_log, "replication": commits}), 201


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "8000")), threaded=True)
