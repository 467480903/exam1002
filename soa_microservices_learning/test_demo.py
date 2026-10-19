import unittest

from microservices import build_microservices
from soa import build_soa


class ArchitectureDemoTest(unittest.TestCase):
    def test_soa_esb_adapts_legacy_contract_and_orchestrates(self):
        esb = build_soa(logger=lambda _: None)
        result = esb.submit_legacy_order({
            "ORDER_NO": "S1", "ITEM_CODE": "book", "QTY": "2",
            "TOTAL_FEE": "88", "SHIP_TO": "上海",
        })
        self.assertEqual("COMPLETED", result["status"])
        self.assertEqual(8, result["inventory"]["remaining"])
        self.assertEqual("SF-S1", result["shipment"]["tracking_no"])

    def test_microservices_publish_event_for_logistics(self):
        orders, logistics = build_microservices(logger=lambda _: None)
        result = orders.create_order({
            "order_id": "M1", "sku": "book", "quantity": 1,
            "amount": 49, "address": "北京",
        })
        self.assertEqual("PAID", result["status"])
        self.assertEqual("M1", logistics.shipments[0]["order_id"])

    def test_inventory_rejects_insufficient_stock(self):
        orders, _ = build_microservices(logger=lambda _: None)
        with self.assertRaisesRegex(ValueError, "库存不足"):
            orders.create_order({
                "order_id": "M2", "sku": "book", "quantity": 99,
                "amount": 1, "address": "深圳",
            })


if __name__ == "__main__":
    unittest.main()

