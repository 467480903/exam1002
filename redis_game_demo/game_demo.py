#!/usr/bin/env python3
"""用 Redis Hash 保存玩家状态，用 Sorted Set 实现实时排行榜。"""

from __future__ import annotations

import argparse
import json
from typing import Any

import redis


PLAYER_PREFIX = "game:player:"
LEADERBOARD_KEY = "game:leaderboard:global"


def player_key(player_id: str) -> str:
    return PLAYER_PREFIX + player_id


def seed(client: redis.Redis) -> None:
    """Pipeline 减少网络往返；transaction=True 使用 MULTI/EXEC 原子提交。"""
    players = [
        {"id": "p1001", "name": "青龙", "x": 120, "y": 88, "hp": 95,
         "equipment": "玄铁剑", "score": 1580},
        {"id": "p1002", "name": "白虎", "x": 45, "y": 210, "hp": 76,
         "equipment": "寒冰弓", "score": 2310},
        {"id": "p1003", "name": "朱雀", "x": 302, "y": 16, "hp": 100,
         "equipment": "烈焰杖", "score": 1980},
        {"id": "p1004", "name": "玄武", "x": 9, "y": 73, "hp": 88,
         "equipment": "磐石盾", "score": 950},
    ]
    with client.pipeline(transaction=True) as pipe:
        pipe.delete(LEADERBOARD_KEY)
        for player in players:
            state = {key: value for key, value in player.items() if key not in {"id", "score"}}
            state["score"] = player["score"]
            pipe.hset(player_key(player["id"]), mapping=state)
            pipe.zadd(LEADERBOARD_KEY, {player["id"]: player["score"]})
        pipe.execute()


def update_score(client: redis.Redis, player_id: str, delta: int) -> int:
    """一次事务同时更新玩家 Hash 和排行榜，避免两个结构短暂不一致。"""
    key = player_key(player_id)
    with client.pipeline(transaction=True) as pipe:
        pipe.hincrby(key, "score", delta)
        pipe.zincrby(LEADERBOARD_KEY, delta, player_id)
        new_hash_score, new_rank_score = pipe.execute()
    assert int(new_hash_score) == int(new_rank_score)
    return int(new_hash_score)


def get_player(client: redis.Redis, player_id: str) -> dict[str, Any]:
    state = client.hgetall(player_key(player_id))
    return {"id": player_id, **state}


def top_n(client: redis.Redis, count: int) -> list[dict[str, Any]]:
    # ZREVRANGE 按分数从高到低；withscores 返回玩家 ID 和分数。
    rows = client.zrevrange(LEADERBOARD_KEY, 0, count - 1, withscores=True)
    return [
        {
            "rank": index,
            "player_id": player_id,
            "name": client.hget(player_key(player_id), "name"),
            "score": int(score),
        }
        for index, (player_id, score) in enumerate(rows, start=1)
    ]


def player_rank(client: redis.Redis, player_id: str) -> dict[str, Any] | None:
    # Redis 排名从 0 开始，业务展示通常从 1 开始。
    rank = client.zrevrank(LEADERBOARD_KEY, player_id)
    score = client.zscore(LEADERBOARD_KEY, player_id)
    if rank is None or score is None:
        return None
    return {"player_id": player_id, "rank": rank + 1, "score": int(score)}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="localhost")
    parser.add_argument("--port", default=6379, type=int)
    args = parser.parse_args()
    client = redis.Redis(host=args.host, port=args.port, decode_responses=True)
    client.ping()

    print("=== 写入玩家 Hash 和排行榜 Sorted Set ===")
    seed(client)
    print("玩家 p1002：")
    print(json.dumps(get_player(client, "p1002"), ensure_ascii=False, indent=2))

    print("\n=== 全服前 3 名 ===")
    print(json.dumps(top_n(client, 3), ensure_ascii=False, indent=2))

    print("\n=== 查询 p1003 的名次 ===")
    print(json.dumps(player_rank(client, "p1003"), ensure_ascii=False, indent=2))

    print("\n=== p1001 获得 1000 积分：Hash 与 ZSet 原子更新 ===")
    print("新积分：", update_score(client, "p1001", 1000))
    print(json.dumps(top_n(client, 4), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

