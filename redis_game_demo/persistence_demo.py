#!/usr/bin/env python3
"""准备并检查 RDB/AOF 非正常重启实验的数据。"""

from __future__ import annotations

import argparse
import json
import time

import redis


RDB = redis.Redis(host="localhost", port=6379, decode_responses=True)
AOF = redis.Redis(host="localhost", port=6380, decode_responses=True)


def info(client: redis.Redis) -> dict[str, object]:
    persistence = client.info("persistence")
    return {
        "rdb_last_save_time": persistence.get("rdb_last_save_time"),
        "aof_enabled": persistence.get("aof_enabled"),
        "aof_last_write_status": persistence.get("aof_last_write_status"),
    }


def seed() -> None:
    for client in (RDB, AOF):
        client.flushall()
        client.set("game:checkpoint", "before-snapshot")

    # RDB 只会恢复这个时间点之前的数据。
    RDB.save()
    RDB.set("game:after-snapshot", "RDB 崩溃后预计丢失")

    # AOF everysec 最坏可能丢失约 1 秒；等待刷盘使本实验结果稳定。
    AOF.set("game:after-snapshot", "AOF 重放后预计保留")
    time.sleep(1.2)

    print("已写入实验数据。持久化状态：")
    print("RDB:", json.dumps(info(RDB), ensure_ascii=False))
    print("AOF:", json.dumps(info(AOF), ensure_ascii=False))
    print("下一步请按照 README 使用 docker compose kill 模拟异常退出。")


def check() -> None:
    for name, client in (("RDB", RDB), ("AOF", AOF)):
        print(f"{name}: checkpoint={client.get('game:checkpoint')!r}, "
              f"after_snapshot={client.get('game:after-snapshot')!r}")
    print("预期：RDB 恢复快照但丢失快照后的键；AOF 重放写命令并保留该键。")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["seed", "check"])
    args = parser.parse_args()
    seed() if args.command == "seed" else check()


if __name__ == "__main__":
    main()

