# Redis 游戏状态、排行榜、持久化与 Sentinel 实验

本项目对应软考系统架构设计师“缓存与 NoSQL 技术选型”材料题，覆盖：

1. 玩家实时状态的数据结构选择；
2. 全服积分排行榜的数据结构选择；
3. RDB 与 AOF 的安全性、恢复速度和性能影响；
4. Redis Sentinel 的监控、故障转移与客户端服务发现。

## 原试题

### 试题四（25 分）

阅读以下关于缓存与 NoSQL 技术选型的说明，并回答问题。

#### 说明

某实时竞技游戏的后台需要管理大量在线玩家的状态（如位置、血量、装备），并维护一个全服实时积分排行榜。当前所有数据直接读写 MySQL，在高峰期不堪重负。技术总监提议引入 Redis，但团队在数据结构选择、持久化配置和高可用架构上存在争议。

### 问题 1（8 分）

请为以下两种游戏数据选择合适的 Redis 数据结构，并说明理由：

1. 玩家实时状态（`player_id` 为键，需要频繁更新位置、血量等字段）。
2. 全服实时积分排行榜（需要能快速按积分排序、获取前 N 名、查询某个玩家的名次）。

### 问题 2（12 分）

团队需要决定 Redis 的持久化策略，以在重启后尽可能恢复数据，同时最小化对性能的影响。请对比 RDB 持久化和 AOF 持久化在数据安全性、重启恢复速度和对性能影响三个方面的特点。

### 问题 3（5 分）

为确保 Redis 服务高可用，团队决定采用 Redis Sentinel（哨兵）模式。请简述哨兵在监控、故障转移和客户端服务发现三个方面的核心功能。

后续章节通过可运行程序依次演示这三个问题涉及的知识点。

## 1. 准备环境

```bash
cd /home/wxf/exam1002/redis_game_demo
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
```

## 2. Hash 保存玩家状态

启动默认的 RDB 和 AOF 实例：

```bash
docker compose up -d
docker compose ps
```

运行数据结构示例：

```bash
python3 game_demo.py
```

玩家状态使用 Redis Hash：

```text
Key: game:player:p1001

name       青龙
x          120
y          88
hp         95
equipment  玄铁剑
score      1580
```

对应命令：

```redis
HSET game:player:p1001 name 青龙 x 120 y 88 hp 95 equipment 玄铁剑 score 1580
HGET game:player:p1001 hp
HSET game:player:p1001 x 130 y 90
HINCRBY game:player:p1001 hp -10
HGETALL game:player:p1001
```

选择 Hash 的理由：

- 玩家状态天然是字段—值结构；
- 可以读取或更新单个字段，不必序列化整个对象；
- `HINCRBY` 等操作具有原子性；
- 相比每个属性一个 Key，更便于管理并减少 Key 数量；
- 相比把整个玩家存成 JSON 字符串，局部修改更加直接。

## 3. Sorted Set 实现排行榜

排行榜使用 Sorted Set：

```text
Key: game:leaderboard:global

member    score
p1002     2310
p1003     1980
p1001     1580
p1004      950
```

常见命令：

```redis
ZADD game:leaderboard:global 1580 p1001
ZINCRBY game:leaderboard:global 1000 p1001
ZREVRANGE game:leaderboard:global 0 9 WITHSCORES
ZREVRANK game:leaderboard:global p1001
ZSCORE game:leaderboard:global p1001
```

- `ZREVRANGE 0 9`：快速取得前 10 名；
- `ZREVRANK`：取得某个玩家从高到低的名次；
- `ZINCRBY`：原子增加积分并自动调整排序；
- Sorted Set 在写入时维护顺序，不需要查询时对所有玩家重新排序。

`game_demo.py` 使用 `MULTI/EXEC` 事务，同时更新玩家 Hash 中的积分和排行榜分数，避免两个结构出现中间不一致状态。

## 4. RDB 与 AOF 对比实验

两个容器配置如下：

| 实例 | 地址 | 配置 |
|---|---|---|
| RDB | `localhost:6379` | 手动快照，关闭 AOF |
| AOF | `localhost:6380` | 关闭快照，`appendfsync everysec` |

准备数据：

```bash
python3 persistence_demo.py seed
```

脚本先写入共同数据，然后对 RDB 执行一次 `SAVE`，最后再向两个实例写入 `game:after-snapshot`。

使用 `kill` 模拟进程异常退出，而不是正常 `SHUTDOWN`：

```bash
docker compose kill redis-rdb redis-aof
docker compose up -d redis-rdb redis-aof
```

等待容器健康后检查恢复结果：

```bash
python3 persistence_demo.py check
```

预期：

```text
RDB: checkpoint='before-snapshot', after_snapshot=None
AOF: checkpoint='before-snapshot', after_snapshot='AOF 重放后预计保留'
```

### RDB 特点

- 周期性生成某一时刻的内存快照；
- 文件紧凑，适合备份和远程灾备；
- 大数据集通常比 AOF 重放恢复更快；
- 父进程 `fork` 子进程生成快照，日常写入性能影响相对小；
- 异常退出会丢失最近一次快照之后的所有修改；
- 数据量很大时，`fork` 和写快照可能造成 CPU、内存和 I/O 峰值。

### AOF 特点

- 追加记录写命令，重启时重放命令恢复数据；
- `appendfsync always` 安全性最高，但每次写入都刷盘，性能影响最大；
- `appendfsync everysec` 通常折中较好，异常时可能丢失约 1 秒数据；
- `appendfsync no` 交给操作系统刷盘，性能高但数据丢失窗口更不可控；
- 文件通常比 RDB 大，恢复需要重放操作，可能更慢；
- AOF rewrite 可以压缩冗余命令，但会消耗 CPU、内存和磁盘 I/O。

### 三方面答题对比

| 方面 | RDB | AOF |
|---|---|---|
| 数据安全性 | 可能丢失上次快照后的数据 | `everysec` 通常最多丢失约 1 秒，`always` 更安全 |
| 重启恢复速度 | 加载紧凑快照，通常较快 | 需要重放 AOF，通常较慢 |
| 写性能影响 | 平时较小，生成快照时有 fork/I/O 开销 | 每次写入追加日志，fsync 越频繁开销越大 |

实际系统可以同时启用 RDB 与 AOF：RDB 适合备份和快速恢复，AOF 用来减少数据丢失。两者同时启用时，Redis 重启优先使用信息更完整的 AOF。

## 5. Sentinel 高可用实验

启动“一主两从＋三个 Sentinel＋实验客户端”：

```bash
docker compose --profile sentinel up -d --build --force-recreate
docker compose --profile sentinel ps
```

Sentinel 配置中启用了：

```redis
sentinel resolve-hostnames yes
sentinel announce-hostnames yes
```

原因是 Compose 网络使用 `redis-primary`、`redis-replica-1` 等服务名。Sentinel 默认不解析主机名；如果未启用，Sentinel 会启动失败，客户端随后会出现 `Temporary failure in name resolution`。

运行客户端发现实验：

```bash
docker compose --profile sentinel exec client python sentinel_demo.py
```

在它观察的 15 秒内，另开终端停止旧主节点：

```bash
docker stop redis-game-primary
```

大约几秒后，三个 Sentinel 会达成多数判断，将一个副本提升为新主节点。再次运行：

```bash
docker compose --profile sentinel exec client python sentinel_demo.py
```

客户端通过逻辑名称 `mymaster` 找到新主节点，不需要把旧主节点地址写死在代码中。

恢复实验环境：

```bash
docker start redis-game-primary
docker compose --profile sentinel down
```

旧主节点恢复后，Sentinel 会将它重新配置为当前主节点的副本，而不是让两个节点同时成为主节点。

### Sentinel 三项核心功能

1. **监控**：Sentinel 周期性向主节点、副本和其他 Sentinel 发送命令，判断实例是否正常；多个 Sentinel 通过主观下线和客观下线机制减少误判。
2. **自动故障转移**：达到 quorum 后，Sentinel 选举领导者，选择合适副本提升为新主节点，将其他副本指向新主节点，并在旧主恢复后把它配置成副本。
3. **客户端服务发现**：客户端向 Sentinel 查询逻辑主节点名，获取当前主节点地址；发生切换后重新查询并连接新主节点。

Sentinel 提供的是非分片 Redis 的高可用，不负责数据分片。海量数据水平分片应考虑 Redis Cluster。

## 6. 高可用设计注意事项

- 至少部署三个 Sentinel，并放在相互独立的故障域；
- quorum 不是 Sentinel 总数，故障转移还需要多数 Sentinel 授权；
- Sentinel 解决可用性问题，RDB/AOF 解决持久性问题，二者不能互相替代；
- Redis 主从复制通常是异步的，故障切换仍可能丢失尚未复制的数据；
- 客户端必须支持 Sentinel，能够重新发现主节点和重连；
- 需要结合超时、重试、幂等、连接池和熔断；
- 生产环境需要认证、TLS、网络隔离、监控和异地备份；
- 排行榜通常可以从 MySQL 权威数据重建，而充值、资产等关键数据不应只保存在 Redis。

## 7. 软考速记

```text
玩家对象字段多、经常局部更新 → Hash
全服积分排序、Top N、查个人名次 → Sorted Set

RDB → 快照、文件小、恢复快、可能丢失一个快照周期
AOF → 写命令日志、安全性高、文件大、恢复较慢、写开销更高

Sentinel → 监控 + 自动故障转移 + 客户端服务发现
```

停止并删除容器：

```bash
docker compose --profile sentinel down
```

同时删除实验数据卷：

```bash
docker compose --profile sentinel down -v
```

