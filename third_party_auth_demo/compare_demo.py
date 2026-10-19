"""连续运行 Kerberos 思想模拟与 PKI 证书认证示例。"""

from kerberos_ticket_demo import run_demo as run_kerberos_demo
from pki_certificate_demo import run_demo as run_pki_demo


def main() -> None:
    print("=" * 18, "Kerberos/KDC 票据模拟", "=" * 18)
    run_kerberos_demo()
    print()
    print("=" * 18, "PKI/CA 证书认证", "=" * 18)
    run_pki_demo()
    print()
    print("结论：Kerberos找KDC拿票；PKI找CA拿证。")


if __name__ == "__main__":
    main()
