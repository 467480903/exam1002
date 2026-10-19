"""两个教学示例的自动化测试。"""

import secrets
import unittest

from cryptography.exceptions import InvalidSignature

from kerberos_ticket_demo import AuthenticationError, ProtectedService, SimpleKDC
from pki_certificate_demo import (
    CertificateError,
    create_ca,
    issue_server_certificate,
    sign_challenge,
    verify_challenge,
    verify_server_certificate,
)


class KerberosIdeaTests(unittest.TestCase):
    def setUp(self):
        self.key = secrets.token_bytes(32)
        self.kdc = SimpleKDC(
            users={"alice": "secret"}, service_keys={"service-a": self.key}
        )

    def test_valid_ticket(self):
        ticket = self.kdc.issue_service_ticket("alice", "secret", "service-a")
        service = ProtectedService("service-a", self.key)
        self.assertEqual(service.verify_ticket(ticket), "alice")

    def test_replayed_ticket_is_rejected(self):
        ticket = self.kdc.issue_service_ticket("alice", "secret", "service-a")
        service = ProtectedService("service-a", self.key)
        service.verify_ticket(ticket)
        with self.assertRaisesRegex(AuthenticationError, "重放"):
            service.verify_ticket(ticket)

    def test_ticket_for_another_service_is_rejected(self):
        ticket = self.kdc.issue_service_ticket("alice", "secret", "service-a")
        wrong_service = ProtectedService("service-b", self.key)
        with self.assertRaisesRegex(AuthenticationError, "不是签发给"):
            wrong_service.verify_ticket(ticket)


class PKITests(unittest.TestCase):
    def setUp(self):
        self.ca_key, self.ca_certificate = create_ca()
        self.server_key, self.server_certificate = issue_server_certificate(
            self.ca_key, self.ca_certificate, "api.factory.local"
        )

    def test_trusted_certificate(self):
        verify_server_certificate(
            self.server_certificate, self.ca_certificate, "api.factory.local"
        )

    def test_certificate_from_untrusted_ca_is_rejected(self):
        _, untrusted_ca = create_ca("Untrusted Root CA")
        with self.assertRaises(CertificateError):
            verify_server_certificate(
                self.server_certificate, untrusted_ca, "api.factory.local"
            )

    def test_challenge_signature(self):
        challenge = b"random-client-challenge"
        signature = sign_challenge(self.server_key, challenge)
        verify_challenge(self.server_certificate, challenge, signature)

    def test_modified_challenge_is_rejected(self):
        challenge = b"random-client-challenge"
        signature = sign_challenge(self.server_key, challenge)
        with self.assertRaises(InvalidSignature):
            verify_challenge(
                self.server_certificate, challenge + b"-modified", signature
            )


if __name__ == "__main__":
    unittest.main()
