"""SOA 示例：ESB 统一适配、路由并编排多个企业服务。"""

from domain import InventoryService, LogisticsService, PaymentService


class EnterpriseServiceBus:
    def __init__(self, inventory, payment, logistics, logger=print):
        self.inventory = inventory
        self.payment = payment
        self.logistics = logistics
        self.log = logger

    def submit_legacy_order(self, legacy_message: dict) -> dict:
        """接收遗留 ERP 风格契约，然后转换为企业标准模型。"""
        self.log("[ESB] 接收 ERP_XML 风格消息，并转换字段")
        order = {
            "order_id": legacy_message["ORDER_NO"],
            "sku": legacy_message["ITEM_CODE"],
            "quantity": int(legacy_message["QTY"]),
            "amount": float(legacy_message["TOTAL_FEE"]),
            "address": legacy_message["SHIP_TO"],
        }

        self.log("[ESB] 路由 -> 库存服务")
        inventory = self.inventory.reserve(order["sku"], order["quantity"])
        self.log("[ESB] 路由 -> 支付服务")
        payment = self.payment.charge(order["order_id"], order["amount"])
        self.log("[ESB] 路由 -> 物流服务")
        shipment = self.logistics.create_shipment(order["order_id"], order["address"])
        return {"order_id": order["order_id"], "status": "COMPLETED",
                "inventory": inventory, "payment": payment, "shipment": shipment}


def build_soa(logger=print):
    return EnterpriseServiceBus(
        InventoryService(), PaymentService(), LogisticsService(), logger
    )

