"""命令行入口：python3 demo.py [soa|microservices]."""

import argparse
import json

from microservices import build_microservices
from soa import build_soa


def run_soa():
    legacy_order = {
        "ORDER_NO": "1001", "ITEM_CODE": "book", "QTY": "2",
        "TOTAL_FEE": "88.0", "SHIP_TO": "上海市浦东新区",
    }
    result = build_soa().submit_legacy_order(legacy_order)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return result


def run_microservices():
    order = {
        "order_id": "1002", "sku": "book", "quantity": 2,
        "amount": 88.0, "address": "上海市浦东新区",
    }
    orders, logistics = build_microservices()
    result = orders.create_order(order)
    result["shipment_created_by_event"] = logistics.shipments[0]
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="SOA 与微服务对比演示")
    parser.add_argument("mode", choices=("soa", "microservices"))
    args = parser.parse_args()
    run_soa() if args.mode == "soa" else run_microservices()

