"""Qdrant 向量数据库教学示例。

演示：创建集合、文本向量化、写入、相似度检索、元数据过滤和简化 RAG。
为了让示例无需下载大型模型，代码使用字符 n-gram 哈希生成教学向量。
生产项目应替换为经过评估的中文或多语言 Embedding 模型。
"""

from __future__ import annotations

import argparse
import hashlib
import math
import re
from dataclasses import dataclass

from qdrant_client import QdrantClient, models


COLLECTION = "robot_knowledge"
VECTOR_SIZE = 384


@dataclass(frozen=True)
class Document:
    id: int
    title: str
    text: str
    category: str
    robot: str


DOCUMENTS = [
    Document(1, "夹爪故障处理", "铝条抓取后发生旋转时，应检查夹持面、抓取中心和夹爪闭合力。专用导向夹爪可以扩大抓取容差。", "故障案例", "G2"),
    Document(2, "双臂推理复盘", "双臂协同增加了动作空间维度，两臂误差会通过长工件耦合。数据不足时可先验证单臂抓取闭环。", "实验记录", "G2"),
    Document(3, "工装定位方案", "放置工位使用导向面和机械限位完成粗定位，再通过二次动作完成精定位。", "机械设计", "G2"),
    Document(4, "VLA安全约束", "模型动作下发前应进行关节限位、速度限制、工作空间和碰撞检查，异常时进入安全状态。", "安全规范", "通用"),
    Document(5, "传统机器人示教", "固定工位可使用示教点和状态机完成确定性控制，适合环境稳定且任务变化较少的场景。", "控制方法", "通用"),
    Document(6, "移动机器人充电", "移动机器人电量低于阈值后，应结束当前任务并导航至充电桩，不适用于机械臂夹爪问题。", "运维规范", "AMR"),
]


def tokens(text: str) -> list[str]:
    """提取英文词、数字及中文字符，并补充相邻二元组。"""
    units = re.findall(r"[a-zA-Z]+(?:[-_.][a-zA-Z0-9]+)*|\d+(?:\.\d+)?|[\u4e00-\u9fff]", text.lower())
    return units + [units[i] + units[i + 1] for i in range(len(units) - 1)]


def embed(text: str) -> list[float]:
    """使用 feature hashing 生成固定维度向量，适合离线教学。"""
    vector = [0.0] * VECTOR_SIZE
    for token in tokens(text):
        digest = hashlib.blake2b(token.encode("utf-8"), digest_size=8).digest()
        value = int.from_bytes(digest, "big")
        index = value % VECTOR_SIZE
        sign = 1.0 if (value >> 8) & 1 else -1.0
        vector[index] += sign

    norm = math.sqrt(sum(value * value for value in vector))
    return [value / norm for value in vector] if norm else vector


def connect(url: str) -> QdrantClient:
    return QdrantClient(url=url, timeout=5)


def init_collection(client: QdrantClient) -> None:
    """重建教学集合，并写入示例文档。"""
    if client.collection_exists(COLLECTION):
        client.delete_collection(COLLECTION)

    client.create_collection(
        collection_name=COLLECTION,
        vectors_config=models.VectorParams(size=VECTOR_SIZE, distance=models.Distance.COSINE),
    )
    client.create_payload_index(
        collection_name=COLLECTION,
        field_name="category",
        field_schema=models.PayloadSchemaType.KEYWORD,
    )
    client.create_payload_index(
        collection_name=COLLECTION,
        field_name="robot",
        field_schema=models.PayloadSchemaType.KEYWORD,
    )

    points = [
        models.PointStruct(
            id=document.id,
            vector=embed(document.title + " " + document.text),
            payload={
                "title": document.title,
                "text": document.text,
                "category": document.category,
                "robot": document.robot,
            },
        )
        for document in DOCUMENTS
    ]
    client.upsert(collection_name=COLLECTION, points=points, wait=True)
    print(f"已创建集合 {COLLECTION!r}，写入 {len(points)} 条数据。")


def search(client: QdrantClient, query: str, robot: str | None, limit: int) -> list:
    query_filter = None
    if robot:
        query_filter = models.Filter(
            must=[models.FieldCondition(key="robot", match=models.MatchValue(value=robot))]
        )

    response = client.query_points(
        collection_name=COLLECTION,
        query=embed(query),
        query_filter=query_filter,
        limit=limit,
        with_payload=True,
    )
    return response.points


def print_results(results: list) -> None:
    if not results:
        print("没有找到结果，请检查过滤条件或先执行 init。")
        return
    for rank, point in enumerate(results, start=1):
        payload = point.payload or {}
        print(f"\n{rank}. {payload.get('title')}  相似度={point.score:.4f}")
        print(f"   分类={payload.get('category')}  机器人={payload.get('robot')}")
        print(f"   {payload.get('text')}")


def rag_answer(query: str, results: list) -> None:
    """展示送给大模型的检索上下文；本示例不调用外部大模型。"""
    print("\n--- 简化 RAG 上下文 ---")
    print(f"用户问题：{query}")
    print("请仅根据以下资料回答；资料不足时明确说明不知道：")
    for index, point in enumerate(results, start=1):
        payload = point.payload or {}
        print(f"[{index}] {payload.get('title')}：{payload.get('text')}")
    print("\n实际系统可把以上内容提交给大语言模型，并要求答案引用 [1]、[2] 等来源。")


def main() -> None:
    parser = argparse.ArgumentParser(description="Qdrant 向量数据库教学程序")
    parser.add_argument("command", choices=["init", "search", "rag"])
    parser.add_argument("query", nargs="?", default="夹爪抓住铝条后为什么会转动")
    parser.add_argument("--robot", help="按 robot 元数据过滤，例如 G2")
    parser.add_argument("--limit", type=int, default=3)
    parser.add_argument("--url", default="http://localhost:6333")
    args = parser.parse_args()

    client = connect(args.url)
    try:
        if args.command == "init":
            init_collection(client)
            return
        if not client.collection_exists(COLLECTION):
            raise RuntimeError("集合不存在，请先运行：python demo.py init")
        results = search(client, args.query, args.robot, args.limit)
        print_results(results)
        if args.command == "rag":
            rag_answer(args.query, results)
    except Exception as exc:
        raise SystemExit(f"操作失败：{exc}\n请确认 Qdrant 已通过 docker compose up -d 启动。") from exc


if __name__ == "__main__":
    main()
