import json
import time

import requests

from src.crypto_utils import public_key_hex, sign_transaction, verify_signature


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
        integrity = state["chain_integrity"]
        print(
            f"{state['node']}: height={state['height']} "
            f"tip={state['tip'][:12]} balances={state['balances']} "
            f"chain_valid={integrity['valid']}"
        )


def print_response(response):
    body = response.json()
    print(f"HTTP {response.status_code}: {json.dumps(body, ensure_ascii=False)}")
    return body


def cryptography_experiment(nonce):
    print("\n" + "=" * 18 + " 1. 密码学 " + "=" * 18)
    unsigned = {"sender": "alice", "receiver": "merchant", "amount": 25, "nonce": nonce}
    signature = sign_transaction(unsigned, "alice")
    print("算法：交易签名 Ed25519；区块链接 SHA-256")
    print("Alice公钥:", public_key_hex("alice")[:32] + "...")
    print("交易签名:", signature[:32] + "...")
    print("本地验签:", verify_signature(unsigned, public_key_hex("alice"), signature))

    tampered = {**unsigned, "amount": 26, "signature": signature}
    print("篡改金额25→26，但继续使用旧签名：")
    response = requests.post(f"{NODES[0]}/transactions", json=tampered, timeout=10)
    body = print_response(response)
    assert response.status_code == 400 and body["reason"] == "数字签名无效"
    return unsigned, signature


def contract_experiment(nonce):
    print("\n" + "=" * 18 + " 2. 智能合约 " + "=" * 18)
    invalid_unsigned = {
        "sender": "alice",
        "receiver": "merchant",
        "amount": -5,
        "nonce": nonce,
    }
    invalid_tx = {
        **invalid_unsigned,
        "signature": sign_transaction(invalid_unsigned, "alice"),
    }
    print("PaymentContract规则：成员、签名、正整数金额、余额、连续nonce")
    print("提交签名正确但金额为-5的交易：")
    response = requests.post(f"{NODES[0]}/transactions", json=invalid_tx, timeout=10)
    body = print_response(response)
    assert response.status_code == 400 and body["reason"] == "支付金额必须是正整数"


def consensus_experiment(unsigned, signature):
    print("\n" + "=" * 18 + " 3. 共识机制 " + "=" * 18)
    features = requests.get(f"{NODES[0]}/features", timeout=3).json()
    consensus = features["consensus"]
    print(
        f"机制：{consensus['type']}，节点数={consensus['nodes']}，"
        f"法定票数={consensus['quorum']}"
    )
    tx = {**unsigned, "signature": signature}
    response = requests.post(f"{NODES[0]}/transactions", json=tx, timeout=10)
    body = response.json()
    print("投票记录：")
    for vote in body.get("votes", []):
        print(" ", json.dumps(vote, ensure_ascii=False))
    print("共识结果：", "达到2/3多数，区块已提交" if body.get("committed") else "未达多数，交易被拒绝")
    assert response.status_code == 201 and body["committed"]
    assert sum(1 for vote in body["votes"] if vote["approve"]) >= consensus["quorum"]
    return body["block"]


def distributed_storage_experiment(committed_block):
    print("\n" + "=" * 18 + " 4. 分布式存储 " + "=" * 18)
    states = [requests.get(f"{url}/state", timeout=3).json() for url in NODES]
    chains = [requests.get(f"{url}/chain", timeout=3).json() for url in NODES]
    for state, chain in zip(states, chains):
        print(
            f"{state['node']}: 独立存储={state['storage']['path']}，"
            f"区块数={len(chain)}，链顶={state['tip'][:12]}...，"
            f"完整性={state['chain_integrity']['reason']}"
        )

    assert all(state["chain_integrity"]["valid"] for state in states)
    assert len({state["tip"] for state in states}) == 1, "节点账本哈希不一致"
    assert all(chain[-1]["hash"] == committed_block["hash"] for chain in chains)
    assert all(chain == chains[0] for chain in chains), "三个节点保存的区块内容不一致"
    print("验证通过：三个独立SQLite副本保存了相同区块，SHA-256链顶一致。")


def main():
    wait_for_nodes()
    initial = requests.get(f"{NODES[0]}/state", timeout=3).json()
    nonce = initial["nonces"]["alice"] + 1
    show_states("实验开始：三个节点分别读取本地SQLite账本")

    unsigned, signature = cryptography_experiment(nonce)
    contract_experiment(nonce)
    block = consensus_experiment(unsigned, signature)
    distributed_storage_experiment(block)
    show_states("实验结束：账户状态已由新区块计算得出")


if __name__ == "__main__":
    main()
