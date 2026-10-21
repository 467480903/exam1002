# 向量数据库入门实验：Qdrant

本项目用一个工业机器人知识库演示向量数据库的基本用法：

1. 将文本转换为固定维度向量；
2. 创建 Qdrant Collection；
3. 写入向量和元数据；
4. 根据自然语言进行相似度检索；
5. 使用元数据过滤结果；
6. 将检索结果组成简化的 RAG 上下文。

## 1. 向量数据库和关系数据库的区别

| 对比项 | 关系数据库 | 向量数据库 |
|---|---|---|
| 典型数据 | 表、行、字段 | 高维向量及其元数据 |
| 主要查询 | 精确条件、范围、关联 | 相似度和最近邻搜索 |
| 示例 | `robot = 'G2'` | 找到语义最接近“夹爪打滑”的文档 |
| 典型索引 | B+树、哈希 | HNSW、IVF、PQ |
| 强项 | 事务、约束、复杂关联 | 非结构化数据的语义检索 |

两者不是替代关系。实际系统通常用关系数据库保存业务和权限数据，用向量数据库保存文本、图像等内容的嵌入向量。

## 2. 文件说明

```text
vector_database_demo/
├── compose.yaml       # 启动 Qdrant 服务
├── demo.py            # 入库、检索、过滤和 RAG 示例
├── requirements.txt   # Python 依赖
└── README.md
```

## 3. 启动实验

在本目录执行：

```bash
docker compose up -d
docker compose ps
```

创建Python虚拟环境并安装客户端：

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

初始化集合和示例数据：

```bash
python demo.py init
```

执行语义检索：

```bash
python demo.py search "夹爪抓住铝条后为什么会转动"
```

增加元数据过滤，只查询G2机器人的资料：

```bash
python demo.py search "怎样提高放置精度" --robot G2
```

查看简化的RAG上下文：

```bash
python demo.py rag "双臂抓取长工件为什么不稳定"
```

Qdrant管理界面：<http://localhost:6333/dashboard>

### 如果出现 `Unknown scheme for proxy URL`

这是系统设置了 `ALL_PROXY=socks://...`，而客户端把访问本机Qdrant的请求也交给了代理。当前示例已在连接代码中设置 `trust_env=False`，访问 `localhost:6333` 时会忽略这些代理变量。

也可以在终端临时设置本机地址不经过代理：

```bash
export NO_PROXY=localhost,127.0.0.1
export no_proxy=localhost,127.0.0.1
```

然后重新执行：

```bash
python demo.py init
```

## 4. 程序运行流程

```text
原始文本
   ↓ embed()
384维向量＋title/category/robot等元数据
   ↓ upsert
Qdrant Collection
   ↓ query_points
相似文档Top-K
   ↓
显示结果，或组成RAG上下文交给大语言模型
```

示例中的 `embed()` 使用字符和二元组的特征哈希，优点是无需联网下载模型，缺点是只能粗略表示词项相似性。它是为了演示向量数据库流程，不是生产级语义模型。生产项目应换成经过业务评测的中文或多语言Embedding模型，并保持入库与查询使用完全相同的模型和维度。

## 5. 重点代码

- `create_collection()`：创建集合并指定向量维数和距离算法；
- `upsert()`：写入或更新向量、ID和元数据；
- `query_points()`：执行最近邻查询；
- `Filter`：按机器人型号等结构化字段过滤；
- `score`：结果相似度，用于排序和阈值判断。

余弦相似度越接近1，通常表示方向越接近。但“相似”不代表“正确”，实际RAG系统还需要重排序、阈值、权限过滤、引用和人工评测。

## 6. 查看服务状态

```bash
curl http://localhost:6333/collections
docker compose logs qdrant
```

## 7. 停止与清理

停止容器并保留数据卷：

```bash
docker compose down
```

停止容器并删除本实验的数据卷：

```bash
docker compose down -v
```

`down -v` 会删除已写入Qdrant的实验数据，需要重新执行 `python demo.py init` 才能恢复。
