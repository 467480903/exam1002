"""Kerberos 核心思想的教学模拟。

这不是 Kerberos 协议实现，不能用于生产环境。示例只保留：
KDC 验证用户、KDC 为服务签发票据、服务验证票据、有效期及重放检测。
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import secrets
import time
from dataclasses import dataclass, field


class AuthenticationError(Exception):
    """身份、票据或签名验证失败。"""


def _encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode("ascii")


def _decode(data: str) -> bytes:
    return base64.urlsafe_b64decode(data.encode("ascii"))


@dataclass
class SimpleKDC:
    """把真实 Kerberos 的 AS/TGS 流程合并后的教学 KDC。"""python kerberos_ticket_demo.py


    users: dict[str, str]
    service_keys: dict[str, bytes]

    def issue_service_ticket(
        self,
        username: str,
        password: str,
        service: str,
        lifetime_seconds: int = 60,
    ) -> str:
        stored_password = self.users.get(username)
        if stored_password is None or not hmac.compare_digest(stored_password, password):
            raise AuthenticationError("用户名或密码错误，KDC拒绝签发票据")

        service_key = self.service_keys.get(service)
        if service_key is None:
            raise AuthenticationError(f"KDC中不存在服务：{service}")

        now = int(time.time())
        payload = {
            "subject": username,
            "audience": service,
            "issued_at": now,
            "expires_at": now + lifetime_seconds,
            "nonce": secrets.token_hex(16),
        }
        payload_bytes = json.dumps(
            payload, sort_keys=True, separators=(",", ":")
        ).encode("utf-8")
        signature = hmac.new(service_key, payload_bytes, hashlib.sha256).digest()
        return f"{_encode(payload_bytes)}.{_encode(signature)}"


@dataclass
class ProtectedService:
    name: str
    shared_key: bytes
    used_nonces: set[str] = field(default_factory=set)

    def verify_ticket(self, ticket: str, now: int | None = None) -> str:
        try:
            payload_part, signature_part = ticket.split(".", maxsplit=1)
            payload_bytes = _decode(payload_part)
            supplied_signature = _decode(signature_part)
            payload = json.loads(payload_bytes)
        except (ValueError, TypeError, json.JSONDecodeError) as exc:
            raise AuthenticationError("票据格式错误") from exc

        expected_signature = hmac.new(
            self.shared_key, payload_bytes, hashlib.sha256
        ).digest()
        if not hmac.compare_digest(expected_signature, supplied_signature):
            raise AuthenticationError("票据签名无效，内容可能被篡改")

        if payload.get("audience") != self.name:
            raise AuthenticationError("票据不是签发给当前服务的")

        current_time = int(time.time()) if now is None else now
        if current_time > int(payload["expires_at"]):
            raise AuthenticationError("票据已经过期")

        nonce = payload["nonce"]
        if nonce in self.used_nonces:
            raise AuthenticationError("检测到票据重放")

        self.used_nonces.add(nonce)
        return str(payload["subject"])


def tamper_ticket(ticket: str) -> str:
    """修改票据载荷但保留旧签名，用于演示完整性校验。"""

    payload_part, signature_part = ticket.split(".", maxsplit=1)
    payload = json.loads(_decode(payload_part))
    payload["subject"] = "mallory"
    modified = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode(
        "utf-8"
    )
    return f"{_encode(modified)}.{signature_part}"


def run_demo() -> None:
    service_key = secrets.token_bytes(32)
    kdc = SimpleKDC(
        users={"alice": "correct-horse-battery-staple"},
        service_keys={"inventory-service": service_key},
    )
    service = ProtectedService("inventory-service", service_key)

    print("1. Alice向KDC证明身份并申请inventory-service票据")
    ticket = kdc.issue_service_ticket(
        "alice", "correct-horse-battery-staple", "inventory-service"
    )
    print("   KDC签发票据成功")

    print("2. Alice向服务提交票据")
    username = service.verify_ticket(ticket)
    print(f"   服务验证成功，当前用户：{username}")

    print("3. 攻击者复制并再次提交相同票据")
    try:
        service.verify_ticket(ticket)
    except AuthenticationError as exc:
        print(f"   验证失败：{exc}")

    print("4. 攻击者修改另一张票据中的用户名")
    another_ticket = kdc.issue_service_ticket(
        "alice", "correct-horse-battery-staple", "inventory-service"
    )
    try:
        service.verify_ticket(tamper_ticket(another_ticket))
    except AuthenticationError as exc:
        print(f"   验证失败：{exc}")


if __name__ == "__main__":
    run_demo()
