from crypto_utils import public_key_hex, verify_signature


GENESIS_BALANCES = {"alice": 100, "bob": 40, "merchant": 0}
MEMBERS = {name: public_key_hex(name) for name in GENESIS_BALANCES}


class PaymentContract:
    """联盟链支付合约：成员身份、签名、余额、金额和 nonce 都必须有效。"""

    @staticmethod
    def validate(tx: dict, balances: dict, next_nonce: int) -> tuple[bool, str]:
        required = {"sender", "receiver", "amount", "nonce", "signature"}
        if not required.issubset(tx):
            return False, "交易字段不完整"
        sender, receiver = tx["sender"], tx["receiver"]
        if sender not in MEMBERS or receiver not in MEMBERS:
            return False, "交易方不是联盟成员"
        if not isinstance(tx["amount"], int) or tx["amount"] <= 0:
            return False, "支付金额必须是正整数"
        if tx["nonce"] != next_nonce:
            return False, f"nonce 应为 {next_nonce}"
        if balances.get(sender, 0) < tx["amount"]:
            return False, "余额不足"
        unsigned = {key: tx[key] for key in ("sender", "receiver", "amount", "nonce")}
        if not verify_signature(unsigned, MEMBERS[sender], tx["signature"]):
            return False, "数字签名无效"
        return True, "合约验证通过"
