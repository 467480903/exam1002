"""与架构无关的业务能力，供两种实现复用。"""


class InventoryService:
    def __init__(self, stock=None):
        self.stock = dict(stock or {"book": 10})

    def reserve(self, sku: str, quantity: int) -> dict:
        if quantity <= 0:
            raise ValueError("quantity 必须大于 0")
        available = self.stock.get(sku, 0)
        if available < quantity:
            raise ValueError(f"库存不足: {sku} 仅剩 {available}")
        self.stock[sku] = available - quantity
        return {"sku": sku, "reserved": quantity, "remaining": self.stock[sku]}


class PaymentService:
    def charge(self, order_id: str, amount: float) -> dict:
        if amount <= 0:
            raise ValueError("amount 必须大于 0")
        return {"order_id": order_id, "amount": amount, "status": "PAID"}


class LogisticsService:
    def __init__(self):
        self.shipments = []

    def create_shipment(self, order_id: str, address: str) -> dict:
        shipment = {
            "order_id": order_id,
            "address": address,
            "tracking_no": f"SF-{order_id}",
            "status": "CREATED",
        }
        self.shipments.append(shipment)
        return shipment

