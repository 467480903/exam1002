#!/usr/bin/env python3
"""客户端不固定连接某个 Redis，而是通过 Sentinel 发现当前主节点。"""

from __future__ import annotations

import json
import time

from redis.sentinel import Sentinel
from redis.sentinel import MasterNotFoundError


SENTINELS = [
    ("sentinel-1", 26379),
    ("sentinel-2", 26379),
    ("sentinel-3", 26379),
]
MASTER_NAME = "mymaster"


def main() -> None:
    sentinel = Sentinel(SENTINELS, socket_timeout=1, decode_responses=True)
    try:
        master_address = sentinel.discover_master(MASTER_NAME)
    except MasterNotFoundError as exc:
        raise SystemExit(
            "无法发现主节点。请先执行：\n"
            "  docker compose --profile sentinel up -d --build --force-recreate\n"
            "再检查：\n"
            "  docker compose --profile sentinel ps -a\n"
            "  docker compose --profile sentinel logs sentinel-1 sentinel-2 sentinel-3\n"
            f"原始错误：{exc}"
        ) from exc
    replicas = sentinel.discover_slaves(MASTER_NAME)
    print("Sentinel 发现的主节点：", master_address)
    print("Sentinel 发现的副本：", replicas)

    # master_for 会在连接失败后再次询问 Sentinel，而不是写死主节点地址。
    master = sentinel.master_for(MASTER_NAME, socket_timeout=1)
    master.hset("game:sentinel:test", mapping={"status": "written-via-sentinel"})
    print("通过当前主节点写入：", json.dumps(master.hgetall("game:sentinel:test"), ensure_ascii=False))

    print("\n持续观察 15 秒；可在另一个终端停止当前主节点以触发故障转移。")
    for _ in range(15):
        try:
            address = sentinel.discover_master(MASTER_NAME)
            print(time.strftime("%H:%M:%S"), "current master =", address)
        except Exception as exc:
            print(time.strftime("%H:%M:%S"), "discovering:", exc)
        time.sleep(1)


if __name__ == "__main__":
    main()

