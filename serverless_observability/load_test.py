#!/usr/bin/env python3
"""制造一次优惠活动流量洪峰，并展示扩缩容、幂等、重试和可观测性。"""

from __future__ import annotations

import concurrent.futures
import json
import time
import urllib.error
import urllib.request
import uuid
from typing import Any


BASE_URL = "http://localhost:8080"


def request(path: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        BASE_URL + path,
        data=data,
        method="GET" if payload is None else "POST",
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            return json.load(response)
    except urllib.error.HTTPError as exc:
        return json.load(exc)


def main() -> None:
    print("1) 初始状态（默认实例数为 0；配置预置实例后会大于 0）")
    print(json.dumps(request("/runtime"), ensure_ascii=False, indent=2))

    print("\n2) 模拟促销活动：24 个请求并发到达")
    with concurrent.futures.ThreadPoolExecutor(max_workers=24) as pool:
        futures = [
            pool.submit(request, f"/api/promotion?user_id=user-{index}")
            for index in range(24)
        ]
        results = [future.result() for future in futures]
    print(f"成功响应：{sum('result' in item for item in results)}/{len(results)}")
    print("流量洪峰后的运行时状态：")
    print(json.dumps(request("/runtime"), ensure_ascii=False, indent=2))

    print("\n3) 模拟充电扣费重复投递：相同 request_id 调用两次")
    request_id = "charge-" + uuid.uuid4().hex[:8]
    payload = {"request_id": request_id, "user_id": "user-1", "amount": 50}
    print(json.dumps(request("/api/charge", payload), ensure_ascii=False, indent=2))
    print(json.dumps(request("/api/charge", payload), ensure_ascii=False, indent=2))
    print("第二次应返回 already_processed，说明幂等键阻止了重复扣费。")

    print("\n4) 模拟函数持续失败：自动重试后写入死信队列")
    failure = request("/api/promotion?user_id=broken-user&fail=1")
    print(json.dumps(failure, ensure_ascii=False, indent=2))

    print("\n5) 三大可观测性支柱中的指标")
    metrics = request("/metrics")
    print(json.dumps(metrics, ensure_ascii=False, indent=2))
    print("故障排查：指标发现失败 → 使用 trace_id 查 traces.jsonl → 查 application.jsonl")

    wait_seconds = request("/runtime")["scale_to_zero_seconds"] + 1
    print(f"\n6) 空闲 {wait_seconds} 秒，观察缩容到预置实例数……")
    time.sleep(wait_seconds)
    print(json.dumps(request("/runtime"), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

