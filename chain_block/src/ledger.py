import json
import sqlite3
from datetime import datetime, timezone

from contract import GENESIS_BALANCES, PaymentContract
from crypto_utils import sha256_hex


class Ledger:
    def __init__(self, path: str):
        self.db = sqlite3.connect(path, check_same_thread=False)
        self.db.execute(
            "CREATE TABLE IF NOT EXISTS blocks (height INTEGER PRIMARY KEY, hash TEXT UNIQUE, body TEXT NOT NULL)"
        )
        self.db.commit()
        if self.height() == -1:
            genesis = {
                "height": 0,
                "previous_hash": "0" * 64,
                "timestamp": "2026-01-01T00:00:00+00:00",
                "proposer": "genesis",
                "transaction": {"type": "genesis", "balances": GENESIS_BALANCES},
                "votes": ["genesis"],
            }
            genesis["hash"] = self.block_hash(genesis)
            self.append(genesis)

    @staticmethod
    def block_hash(block: dict) -> str:
        return sha256_hex({key: value for key, value in block.items() if key != "hash"})

    def blocks(self) -> list[dict]:
        rows = self.db.execute("SELECT body FROM blocks ORDER BY height").fetchall()
        return [json.loads(row[0]) for row in rows]

    def height(self) -> int:
        return self.db.execute("SELECT COALESCE(MAX(height), -1) FROM blocks").fetchone()[0]

    def tip_hash(self) -> str:
        row = self.db.execute("SELECT hash FROM blocks ORDER BY height DESC LIMIT 1").fetchone()
        return row[0] if row else "0" * 64

    def state(self) -> tuple[dict, dict]:
        balances = dict(GENESIS_BALANCES)
        nonces = {name: 0 for name in balances}
        for block in self.blocks()[1:]:
            tx = block["transaction"]
            balances[tx["sender"]] -= tx["amount"]
            balances[tx["receiver"]] += tx["amount"]
            nonces[tx["sender"]] = tx["nonce"]
        return balances, nonces

    def validate_tx(self, tx: dict) -> tuple[bool, str]:
        balances, nonces = self.state()
        return PaymentContract.validate(tx, balances, nonces.get(tx.get("sender"), 0) + 1)

    def make_block(self, tx: dict, proposer: str, votes: list[str]) -> dict:
        block = {
            "height": self.height() + 1,
            "previous_hash": self.tip_hash(),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "proposer": proposer,
            "transaction": tx,
            "votes": sorted(votes),
        }
        block["hash"] = self.block_hash(block)
        return block

    def validate_block(self, block: dict, quorum: int) -> tuple[bool, str]:
        if block.get("height") != self.height() + 1:
            return False, "区块高度错误"
        if block.get("previous_hash") != self.tip_hash():
            return False, "前一区块哈希不匹配"
        if block.get("hash") != self.block_hash(block):
            return False, "区块哈希无效"
        if len(set(block.get("votes", []))) < quorum:
            return False, "赞成票不足"
        return self.validate_tx(block.get("transaction", {}))

    def append(self, block: dict) -> None:
        self.db.execute(
            "INSERT INTO blocks(height, hash, body) VALUES (?, ?, ?)",
            (block["height"], block["hash"], json.dumps(block, sort_keys=True)),
        )
        self.db.commit()
