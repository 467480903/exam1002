"""使用内存密钥和证书演示 PKI 第三方认证。

示例创建教学根 CA，由 CA 签发服务器证书，再完成一次挑战—响应认证。
所有密钥只存在于当前进程内，程序退出后即丢失。
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from cryptography import x509
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from cryptography.x509.oid import ExtendedKeyUsageOID, NameOID


class CertificateError(Exception):
    """证书信任或身份校验失败。"""


def create_ca(common_name: str = "Demo Root CA"):
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, common_name)])
    now = datetime.now(timezone.utc)
    certificate = (
        x509.CertificateBuilder()
        .subject_name(name)
        .issuer_name(name)
        .public_key(private_key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now - timedelta(minutes=1))
        .not_valid_after(now + timedelta(days=365))
        .add_extension(
            x509.BasicConstraints(ca=True, path_length=0), critical=True
        )
        .add_extension(
            x509.KeyUsage(
                digital_signature=True,
                content_commitment=False,
                key_encipherment=False,
                data_encipherment=False,
                key_agreement=False,
                key_cert_sign=True,
                crl_sign=True,
                encipher_only=False,
                decipher_only=False,
            ),
            critical=True,
        )
        .sign(private_key, hashes.SHA256())
    )
    return private_key, certificate


def issue_server_certificate(ca_key, ca_certificate, hostname: str):
    server_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    now = datetime.now(timezone.utc)
    subject = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, hostname)])
    certificate = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(ca_certificate.subject)
        .public_key(server_key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now - timedelta(minutes=1))
        .not_valid_after(now + timedelta(days=30))
        .add_extension(x509.BasicConstraints(ca=False, path_length=None), critical=True)
        .add_extension(
            x509.SubjectAlternativeName([x509.DNSName(hostname)]), critical=False
        )
        .add_extension(
            x509.ExtendedKeyUsage([ExtendedKeyUsageOID.SERVER_AUTH]), critical=False
        )
        .sign(ca_key, hashes.SHA256())
    )
    return server_key, certificate


def verify_server_certificate(
    certificate: x509.Certificate,
    trusted_ca: x509.Certificate,
    expected_hostname: str,
    now: datetime | None = None,
) -> None:
    moment = datetime.now(timezone.utc) if now is None else now
    if certificate.issuer != trusted_ca.subject:
        raise CertificateError("证书颁发者不是受信任的CA")

    try:
        trusted_ca.public_key().verify(
            certificate.signature,
            certificate.tbs_certificate_bytes,
            padding.PKCS1v15(),
            certificate.signature_hash_algorithm,
        )
    except InvalidSignature as exc:
        raise CertificateError("证书上的CA签名无效") from exc

    if not (certificate.not_valid_before_utc <= moment <= certificate.not_valid_after_utc):
        raise CertificateError("证书不在有效期内")

    try:
        names = certificate.extensions.get_extension_for_class(
            x509.SubjectAlternativeName
        ).value.get_values_for_type(x509.DNSName)
    except x509.ExtensionNotFound as exc:
        raise CertificateError("证书缺少Subject Alternative Name") from exc

    if expected_hostname not in names:
        raise CertificateError("证书中的服务器名称不匹配")

    try:
        usage = certificate.extensions.get_extension_for_class(
            x509.ExtendedKeyUsage
        ).value
    except x509.ExtensionNotFound as exc:
        raise CertificateError("证书缺少扩展密钥用途") from exc
    if ExtendedKeyUsageOID.SERVER_AUTH not in usage:
        raise CertificateError("证书不允许用于服务器认证")


def sign_challenge(server_key, challenge: bytes) -> bytes:
    return server_key.sign(
        challenge,
        padding.PSS(
            mgf=padding.MGF1(hashes.SHA256()),
            salt_length=padding.PSS.MAX_LENGTH,
        ),
        hashes.SHA256(),
    )


def verify_challenge(
    certificate: x509.Certificate, challenge: bytes, signature: bytes
) -> None:
    certificate.public_key().verify(
        signature,
        challenge,
        padding.PSS(
            mgf=padding.MGF1(hashes.SHA256()),
            salt_length=padding.PSS.MAX_LENGTH,
        ),
        hashes.SHA256(),
    )


def run_demo() -> None:
    print("1. 创建受客户端信任的教学根CA")
    ca_key, ca_certificate = create_ca()

    print("2. CA为api.factory.local签发服务器证书")
    server_key, server_certificate = issue_server_certificate(
        ca_key, ca_certificate, "api.factory.local"
    )

    print("3. 客户端使用受信任CA公钥验证服务器证书")
    verify_server_certificate(
        server_certificate, ca_certificate, "api.factory.local"
    )
    print("   证书签名、有效期、用途和主机名验证成功")

    print("4. 客户端发送随机挑战，服务器使用私钥签名")
    challenge = b"client-random-challenge-2026"
    signature = sign_challenge(server_key, challenge)
    verify_challenge(server_certificate, challenge, signature)
    print("   挑战签名验证成功，服务器证明其持有证书对应的私钥")

    print("5. 攻击者篡改挑战内容")
    try:
        verify_challenge(server_certificate, challenge + b"-tampered", signature)
    except InvalidSignature:
        print("   验证失败：数据已变化，原签名不再有效")


if __name__ == "__main__":
    run_demo()
