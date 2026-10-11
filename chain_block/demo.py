import json
import time

import requests

from src.crypto_utils import sign_transaction


NODES = ["http://127.0.0.1:8001", "http://127.0.0.1:8002", "http://127.0.0.1:8003"]


def wait_for_nodes():
    for node in NODES:
        for _ in range(30):
            try:
                if requests.get(f"{node}/health", timeout=1).ok:
                    break
            except requests.RequestException:
                time.sleep(1)
        else:
            raise RuntimeError(f"节点未就绪: {node}")


def show_states(title):
    print(f"\n=== {title} ===")
    for url in NODES:
        state = requests.get(f"{url}/state", timeout=3).json()
        print(f"{state['node']}: height={state['height']} tip={state['tip'][:12]} balances={state['balances']}")


def main():
    wait_for_nodes()
    show_states("支付前：三个节点各自读取本地 SQLite 账本")

    unsigned = {"sender": "alice", "receiver": "merchant", "amount": 25, "nonce": 1}
    tx = {**unsigned, "signature": sign_transaction(unsigned, "alice")}
    print("\nAlice 发起联盟链支付：25 -> merchant")
    print("数字签名:", tx["signature"][:32] + "...")
    result = requests.post(f"{NODES[0]}/transactions", json=tx, timeout=10)
    body = result.json()
    print("\n投票记录:")
    for vote in body.get("votes", []):
        print(" ", json.dumps(vote, ensure_ascii=False))
    print("共识结果:", "已提交" if body.get("committed") else "被拒绝")
    show_states("支付后：多数共识区块已复制到三个节点")

    states = [requests.get(f"{url}/state", timeout=3).json() for url in NODES]
    assert len({state["tip"] for state in states}) == 1, "节点账本哈希不一致"
    assert all(state["balances"]["alice"] == 75 for state in states)
    assert all(state["balances"]["merchant"] == 25 for state in states)
    print("\n验证通过：三个独立节点的区块哈希与账户余额完全一致。")


if __name__ == "__main__":
    main()
