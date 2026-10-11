import hashlib
import json

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey
from cryptography.exceptions import InvalidSignature


# 固定种子仅为保证每次教学演示结果一致，生产环境绝不能硬编码私钥。
DEMO_SEEDS = {
    "alice": bytes.fromhex("11" * 32),
    "bob": bytes.fromhex("22" * 32),
    "merchant": bytes.fromhex("33" * 32),
}


def canonical_json(data: dict) -> bytes:
    return json.dumps(data, sort_keys=True, separators=(",", ":")).encode("utf-8")


def private_key(name: str) -> Ed25519PrivateKey:
    return Ed25519PrivateKey.from_private_bytes(DEMO_SEEDS[name])


def public_key_hex(name: str) -> str:
    return private_key(name).public_key().public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    ).hex()


def sign_transaction(unsigned: dict, name: str) -> str:
    return private_key(name).sign(canonical_json(unsigned)).hex()


def verify_signature(unsigned: dict, public_hex: str, signature_hex: str) -> bool:
    try:
        Ed25519PublicKey.from_public_bytes(bytes.fromhex(public_hex)).verify(
            bytes.fromhex(signature_hex), canonical_json(unsigned)
        )
        return True
    except (InvalidSignature, ValueError, TypeError):
        return False


def sha256_hex(data: dict) -> str:
    return hashlib.sha256(canonical_json(data)).hexdigest()
