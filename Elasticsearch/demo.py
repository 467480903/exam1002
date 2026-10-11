#!/usr/bin/env python3
"""用同一批商品数据横向比较 SQLite 与 Elasticsearch。

本程序只用于教学：SQLite 是权威事务库，Elasticsearch 是搜索索引。
"""

from __future__ import annotations

import json
import sqlite3
import sys
from pathlib import Path
from typing import Any, Iterable

from elasticsearch import Elasticsearch, helpers
from elasticsearch.exceptions import ConnectionError as ElasticsearchConnectionError


BASE_DIR = Path(__file__).resolve().parent
SQLITE_PATH = BASE_DIR / "demo.db"
ES_URL = "http://localhost:9200"
INDEX_NAME = "products"

PRODUCTS = [
    {
        "id": 1,
        "name": "无线降噪蓝牙耳机",
        "description": "适合通勤的主动降噪耳机，支持蓝牙连接和长续航",
        "category": "数码",
        "price": 299.0,
        "stock": 30,
    },
    {
        "id": 2,
        "name": "运动蓝牙耳机",
        "description": "防水轻量设计，适合跑步，不支持主动降噪",
        "category": "数码",
        "price": 159.0,
        "stock": 50,
    },
    {
        "id": 3,
        "name": "机械键盘",
        "description": "有线机械键盘，适合办公和编程",
        "category": "数码",
        "price": 399.0,
        "stock": 18,
    },
    {
        "id": 4,
        "name": "软件架构设计教程",
        "description": "介绍分布式系统、数据库、缓存和搜索引擎架构",
        "category": "图书",
        "price": 89.0,
        "stock": 100,
    },
    {
        "id": 5,
        "name": "Elasticsearch 实战",
        "description": "学习全文检索、倒排索引、分片、副本和聚合分析",
        "category": "图书",
        "price": 108.0,
        "stock": 45,
    },
    {
        "id": 6,
        "name": "便携蓝牙音箱",
        "description": "户外便携音箱，支持蓝牙连接和防水功能",
        "category": "数码",
        "price": 219.0,
        "stock": 0,
    },
]


def title(text: str) -> None:
    print(f"\n{'=' * 15} {text} {'=' * 15}")


def pretty(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2)


def connect_sqlite() -> sqlite3.Connection:
    connection = sqlite3.connect(SQLITE_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def connect_elasticsearch() -> Elasticsearch:
    client = Elasticsearch(ES_URL, request_timeout=10)
    try:
        if not client.ping():
            raise ElasticsearchConnectionError("ping 返回 false")
    except ElasticsearchConnectionError as exc:
        print("无法连接 Elasticsearch。请先执行：docker compose up -d")
        print(f"地址：{ES_URL}；错误：{exc}")
        raise SystemExit(1) from exc
    return client


def initialize_sqlite(connection: sqlite3.Connection) -> None:
    connection.executescript(
        """
        DROP TABLE IF EXISTS products;
        CREATE TABLE products (
            id          INTEGER PRIMARY KEY,
            name        TEXT NOT NULL,
            description TEXT NOT NULL,
            category    TEXT NOT NULL,
            price       REAL NOT NULL CHECK (price >= 0),
            stock       INTEGER NOT NULL CHECK (stock >= 0)
        );
        CREATE INDEX idx_products_category_price
            ON products(category, price);
        """
    )
    connection.executemany(
        """INSERT INTO products
           (id, name, description, category, price, stock)
           VALUES (:id, :name, :description, :category, :price, :stock)""",
        PRODUCTS,
    )
    connection.commit()


def initialize_elasticsearch(client: Elasticsearch) -> None:
    if client.indices.exists(index=INDEX_NAME):
        client.indices.delete(index=INDEX_NAME)

    # text 用于全文检索；keyword 用于精确过滤、排序和聚合。
    client.indices.create(
        index=INDEX_NAME,
        mappings={
            "properties": {
                "name": {
                    "type": "text",
                    "fields": {"keyword": {"type": "keyword"}},
                },
                "description": {"type": "text"},
                "category": {"type": "keyword"},
                "price": {"type": "double"},
                "stock": {"type": "integer"},
            }
        },
    )

    actions = [
        {
            "_index": INDEX_NAME,
            "_id": product["id"],
            "_source": {key: value for key, value in product.items() if key != "id"},
        }
        for product in PRODUCTS
    ]
    helpers.bulk(client, actions)
    # Elasticsearch 默认近实时；教学程序主动 refresh，保证后续立即能搜到。
    client.indices.refresh(index=INDEX_NAME)


def rows_to_dicts(rows: Iterable[sqlite3.Row]) -> list[dict[str, Any]]:
    return [dict(row) for row in rows]


def demo_exact_lookup(connection: sqlite3.Connection, client: Elasticsearch) -> None:
    title("1. 按主键精确查询")
    sql = "SELECT * FROM products WHERE id = ?"
    sql_result = dict(connection.execute(sql, (5,)).fetchone())
    es_result = client.get(index=INDEX_NAME, id="5")

    print("SQLite SQL:", sql)
    print(pretty(sql_result))
    print("Elasticsearch: GET /products/_doc/5")
    print(pretty({"id": es_result["_id"], **es_result["_source"]}))
    print("结论：两者都适合按唯一 ID 查询；SQLite 还能提供事务和约束。")


def demo_filter(connection: sqlite3.Connection, client: Elasticsearch) -> None:
    title("2. 精确过滤、范围查询和排序")
    sql = """SELECT * FROM products
             WHERE category = ? AND price <= ? AND stock > 0
             ORDER BY price ASC"""
    sql_result = rows_to_dicts(connection.execute(sql, ("数码", 300)).fetchall())

    query = {
        "bool": {
            "filter": [
                {"term": {"category": "数码"}},
                {"range": {"price": {"lte": 300}}},
                {"range": {"stock": {"gt": 0}}},
            ]
        }
    }
    response = client.search(
        index=INDEX_NAME,
        query=query,
        sort=[{"price": "asc"}],
        size=20,
    )
    es_result = [
        {"id": int(hit["_id"]), **hit["_source"]}
        for hit in response["hits"]["hits"]
    ]

    print("SQLite SQL:\n", sql)
    print(pretty(sql_result))
    print("Elasticsearch Query DSL:\n", pretty(query))
    print(pretty(es_result))
    print("结论：结构化过滤两者都能完成；SQLite 的 SQL 更紧凑。")


def demo_full_text(connection: sqlite3.Connection, client: Elasticsearch) -> None:
    title("3. 全文搜索与相关性")
    keyword = "蓝牙 降噪"
    like_pattern = "%蓝牙%"
    sql = """SELECT * FROM products
             WHERE name LIKE ? OR description LIKE ?"""
    sql_result = rows_to_dicts(
        connection.execute(sql, (like_pattern, like_pattern)).fetchall()
    )

    query = {
        "multi_match": {
            "query": keyword,
            "fields": ["name^3", "description"],
            "type": "best_fields",
        }
    }
    response = client.search(
        index=INDEX_NAME,
        query=query,
        highlight={"fields": {"name": {}, "description": {}}},
        size=20,
    )
    es_result = [
        {
            "id": hit["_id"],
            "score": round(hit["_score"], 3),
            "name": hit["_source"]["name"],
            "highlight": hit.get("highlight", {}),
        }
        for hit in response["hits"]["hits"]
    ]

    print("SQLite 使用 LIKE，只判断字符串是否出现：\n", sql)
    print(pretty(sql_result))
    print("Elasticsearch 使用 multi_match，并让 name 字段权重乘 3：")
    print(pretty(query))
    print(pretty(es_result))
    print("结论：Elasticsearch 能分词、打分、加权和高亮，这是核心优势。")


def demo_aggregation(connection: sqlite3.Connection, client: Elasticsearch) -> None:
    title("4. 分组聚合")
    sql = """SELECT category, COUNT(*) AS count, ROUND(AVG(price), 2) AS avg_price
             FROM products GROUP BY category ORDER BY category"""
    sql_result = rows_to_dicts(connection.execute(sql).fetchall())

    response = client.search(
        index=INDEX_NAME,
        size=0,
        aggs={
            "by_category": {
                "terms": {"field": "category"},
                "aggs": {"avg_price": {"avg": {"field": "price"}}},
            }
        },
    )
    es_result = [
        {
            "category": bucket["key"],
            "count": bucket["doc_count"],
            "avg_price": round(bucket["avg_price"]["value"], 2),
        }
        for bucket in response["aggregations"]["by_category"]["buckets"]
    ]

    print("SQLite GROUP BY:\n", sql)
    print(pretty(sql_result))
    print("Elasticsearch Aggregations:")
    print(pretty(es_result))
    print("结论：两者都能聚合；Elasticsearch 擅长在海量搜索结果上实时统计。")


def demo_transaction(connection: sqlite3.Connection, client: Elasticsearch) -> None:
    title("5. 事务能力对比")
    before = connection.execute(
        "SELECT stock FROM products WHERE id = 1"
    ).fetchone()["stock"]
    try:
        connection.execute("BEGIN")
        connection.execute("UPDATE products SET stock = stock - 1 WHERE id = 1")
        raise RuntimeError("模拟支付失败")
    except RuntimeError:
        connection.rollback()
    after = connection.execute(
        "SELECT stock FROM products WHERE id = 1"
    ).fetchone()["stock"]

    es_document = client.get(index=INDEX_NAME, id="1")
    print(f"SQLite 事务回滚：库存修改前={before}，回滚后={after}")
    print(f"Elasticsearch 文档版本号 _version={es_document['_version']}")
    print(
        "Elasticsearch 对单文档更新具有原子性，并支持乐观并发控制；"
        "但不提供 SQLite 那样的通用多行 ACID 事务。"
    )
    print("架构实践：订单、余额、库存以事务数据库为准，搜索数据异步同步到 ES。")


def print_architecture() -> None:
    title("推荐的实际系统架构")
    print(
        """
用户写请求 → SQLite/MySQL/PostgreSQL（权威数据、事务）
                         │
                         ├─ 消息队列 / CDC / Outbox
                         ↓
                  Elasticsearch（搜索副本）
                         ↓
                 全文检索、过滤、聚合

注意：Elasticsearch 搜索索引可以重建，不应把它当作支付账本。
""".strip()
    )


def main() -> None:
    client = connect_elasticsearch()
    with connect_sqlite() as connection:
        title("初始化相同的测试数据")
        initialize_sqlite(connection)
        initialize_elasticsearch(client)
        print(f"SQLite: {SQLITE_PATH}")
        print(f"Elasticsearch: {ES_URL}/{INDEX_NAME}")
        print(f"已分别写入 {len(PRODUCTS)} 条商品数据。")

        demo_exact_lookup(connection, client)
        demo_filter(connection, client)
        demo_full_text(connection, client)
        demo_aggregation(connection, client)
        demo_transaction(connection, client)
        print_architecture()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(130)

