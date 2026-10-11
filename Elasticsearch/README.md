# Elasticsearch 与 SQLite 横向对比实验

本实验面向软件架构设计师考试复习。它把同一批商品数据分别写入：

- **SQLite**：代表关系型、事务型数据库；
- **Elasticsearch**：代表分布式搜索与分析引擎。

程序会依次比较主键查询、条件过滤、全文检索、聚合分析和事务能力。

> `compose.yaml` 为了简化本地学习关闭了认证，只能用于本机实验，不能用于生产。

## 1. 目录结构

```text
Elasticsearch/
├── compose.yaml          # 单节点 Elasticsearch 9.5.5
├── demo.py               # SQLite 与 Elasticsearch 对比程序
├── requirements.txt      # Python Elasticsearch 客户端
├── rest_examples.http    # 可以逐条执行的 REST API
└── README.md
```

SQLite 由 Python 标准库提供，不需要另外安装服务。Elasticsearch 使用 Docker，是一个单节点集群。

## 2. 运行实验

进入本目录：

```bash
cd /home/wxf/exam1002/Elasticsearch
```

启动 Elasticsearch：

```bash
docker compose up -d
docker compose ps
```

第一次需要下载较大的 Elasticsearch 镜像。等待健康检查通过后安装 Python 依赖：

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
```

执行对比程序：

```bash
python3 demo.py
```

程序每次运行都会重新创建 `demo.db` 和 `products` 索引，结果可以重复验证。

完成实验后停止容器：

```bash
docker compose down
```

连同实验数据一起删除：

```bash
docker compose down -v
```

## 3. 两种数据库的定位

| 比较项 | SQLite | Elasticsearch |
|---|---|---|
| 核心定位 | 关系型事务数据库 | 分布式搜索与分析引擎 |
| 数据模型 | 表、行、列 | Index 中的 JSON Document |
| 查询语言 | SQL | Query DSL、ES\|QL、SQL 等 |
| 全文检索 | 基础 LIKE；可选 FTS | 核心能力，倒排索引 |
| 相关性评分 | 无 | 有 `_score` |
| 事务 | 支持 ACID 事务 | 单文档原子，不提供通用多文档 ACID 事务 |
| JOIN | 支持 | 能力受限，通常采用反规范化 |
| 扩展方式 | 主要为单机嵌入式 | 原生集群、分片和副本 |
| 数据可见性 | 事务提交后可查询 | 默认近实时，需要 refresh 后可搜索 |
| 典型用途 | 订单、账户、库存、配置 | 搜索、日志、指标、聚合、向量检索 |

不要简单地认为 Elasticsearch 比关系数据库“更高级”。二者解决的问题不同。

## 4. 核心名词对应

| Elasticsearch | 近似的关系数据库概念 | 说明 |
|---|---|---|
| Cluster | 数据库集群 | 一个或多个节点组成 |
| Node | 数据库服务器实例 | 集群中的一个 ES 进程 |
| Index | 表 | 一类文档的逻辑集合，但并不完全等于表 |
| Document | 行 | 一个 JSON 文档 |
| Field | 列 | 文档中的字段 |
| Mapping | Schema | 字段类型及索引规则 |
| Shard | 数据分区 | 每个分片本身是一个 Lucene 索引 |
| Replica | 副本 | 容错并提高读吞吐量 |

## 5. Mapping：`text` 与 `keyword`

本实验的 Mapping 包含：

```json
{
  "name": {
    "type": "text",
    "fields": {
      "keyword": {"type": "keyword"}
    }
  },
  "description": {"type": "text"},
  "category": {"type": "keyword"},
  "price": {"type": "double"},
  "stock": {"type": "integer"}
}
```

- `text` 会经过分析器和分词器，用于全文搜索；
- `keyword` 保留完整值，用于精确匹配、排序和聚合；
- 同一个字段可以同时拥有 `text` 主字段和 `keyword` 子字段；
- `match` 通常查询 `text`；`term` 通常查询 `keyword`、数字和状态值。

常见错误是对 `text` 字段使用 `term` 查询，或者直接对 `text` 字段做聚合。

## 6. 倒排索引

关系数据库的普通索引通常从一条记录的字段值找到记录：

```text
商品ID 5 → Elasticsearch 实战
```

倒排索引从词项找到包含它的文档：

```text
全文检索 → 文档5
倒排索引 → 文档5
蓝牙     → 文档1、文档2、文档6
```

Elasticsearch 搜索时主要查询预先建立的倒排索引，而不是逐文档执行 `%关键词%` 字符串扫描。

## 7. `query` 与 `filter`

Query DSL 中要区分两种上下文：

- **query context**：判断是否匹配，同时计算相关性 `_score`；
- **filter context**：只回答“是或否”，不计算相关性，适合类别、状态、价格范围等条件。

示例：

```json
{
  "query": {
    "bool": {
      "must": [
        {"match": {"description": "蓝牙耳机"}}
      ],
      "filter": [
        {"term": {"category": "数码"}},
        {"range": {"price": {"lte": 300}}}
      ]
    }
  }
}
```

考试和架构设计中，应将不需要参与相关性评分的精确条件放入 `filter`。

## 8. 分片和副本

```text
products index
├── Primary Shard 0
│   └── Replica Shard 0
├── Primary Shard 1
│   └── Replica Shard 1
└── ...
```

- 主分片负责保存数据；
- 副本分片是主分片的完整复制；
- 分片可以分布在不同节点上，实现水平扩展；
- 副本不能与对应主分片位于同一个节点；
- 副本提供故障恢复能力，也可以分担读查询；
- 主分片数量应提前规划，副本数量可以动态调整。

这个实验只有一个节点，因此不能在其他节点上安置副本。生产系统通常使用多节点集群。

## 9. 近实时搜索

Elasticsearch 写入成功与“已经能被搜索到”不是完全相同的时刻。新文档通常经过 `refresh` 后才可搜索，因此称为近实时搜索。

`demo.py` 批量写入后主动执行：

```python
client.indices.refresh(index="products")
```

生产程序不应在每次写入后都强制 refresh，否则会降低写入性能。

## 10. 正确的业务架构

```text
                 写入订单
用户 ─────────────────────────→ 事务数据库
                                  │
                                  │ CDC / Outbox / 消息队列
                                  ↓
                              Elasticsearch
                                  ↑
用户 ───── 搜索、过滤、统计 ──────┘
```

推荐原则：

1. SQLite、MySQL 或 PostgreSQL 保存权威业务数据；
2. Elasticsearch 保存可重新构建的搜索副本；
3. 通过 CDC、消息队列或 Outbox 模式同步数据；
4. 接受事务库与搜索索引之间短暂的最终一致性；
5. 不要使用 Elasticsearch 直接承担余额、支付和订单事务。

## 11. 软考重点速记

1. Elasticsearch 基于 Lucene，是分布式搜索和分析引擎；
2. 使用倒排索引提高全文检索效率；
3. 集群由节点组成，Index 被拆分成 Shard；
4. Replica 提高可用性和读吞吐量；
5. `text` 用于分词检索，`keyword` 用于精确查询和聚合；
6. Query DSL 支持全文查询、布尔组合、范围过滤和聚合；
7. 搜索结果可以根据相关性 `_score` 排序；
8. Elasticsearch 是近实时搜索系统；
9. Elasticsearch 强于全文搜索和分布式分析，弱于关系事务和 JOIN；
10. 实际项目通常采用“事务数据库＋Elasticsearch 搜索副本”。

## 12. 建议练习

运行一次 `demo.py` 后，尝试：

1. 修改 `multi_match` 中 `name^3` 的权重，观察排序变化；
2. 把 `category` 从 `keyword` 改成 `text`，观察 `term` 和聚合的变化；
3. 删除程序中的 `refresh`，观察写入后立即搜索的差异；
4. 在 `PRODUCTS` 中增加数据并添加品牌字段；
5. 使用 `rest_examples.http` 查看分词结果和分片状态；
6. 将副本数设为 1，观察单节点集群为何显示黄色健康状态。

