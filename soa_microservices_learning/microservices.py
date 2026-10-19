"""微服务示例：独立 API 协作，领域事件解耦后续处理。"""

from collections import defaultdict

from domain import InventoryService, LogisticsService, PaymentService


class EventBus:
    def __init__(self, logger=print):
        self.handlers = defaultdict(list)
        self.log = logger

    def subscribe(self, event_name, handler):
        self.handlers[event_name].append(handler)

    def publish(self, event_name, payload):
        self.log(f"[事件总线] 发布 {event_name}")
        for handler in self.handlers[event_name]:
            handler(payload)


class InventoryAPI:
    def __init__(self, service, logger=print):
        self.service, self.log = service, logger

    def post_reservations(self, request):
        self.log("[库存服务 API] POST /reservations")
        return self.service.reserve(request["sku"], request["quantity"])


class PaymentAPI:
    def __init__(self, service, logger=print):
        self.service, self.log = service, logger

    def post_payments(self, request):
        self.log("[支付服务 API] POST /payments")
        return self.service.charge(request["order_id"], request["amount"])


class LogisticsEventHandler:
    def __init__(self, service, logger=print):
        self.service, self.log = service, logger

    def when_order_paid(self, event):
        self.log("[物流服务] 消费 OrderPaid，不依赖订单服务内部实现")
        self.service.create_shipment(event["order_id"], event["address"])


class OrderService:
    def __init__(self, inventory_api, payment_api, event_bus, logger=print):
        self.inventory_api = inventory_api
        self.payment_api = payment_api
        self.event_bus = event_bus
        self.log = logger

    def create_order(self, request):
        self.log("[订单服务] POST /orders")
        inventory = self.inventory_api.post_reservations(request)
        payment = self.payment_api.post_payments(request)
        self.event_bus.publish("OrderPaid", {
            "order_id": request["order_id"], "address": request["address"]
        })
        return {"order_id": request["order_id"], "status": "PAID",
                "inventory": inventory, "payment": payment}


def build_microservices(logger=print):
    bus = EventBus(logger)
    logistics = LogisticsService()
    handler = LogisticsEventHandler(logistics, logger)
    bus.subscribe("OrderPaid", handler.when_order_paid)
    orders = OrderService(
        InventoryAPI(InventoryService(), logger),
        PaymentAPI(PaymentService(), logger),
        bus,
        logger,
    )
    return orders, logistics

