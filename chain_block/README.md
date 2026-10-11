# 三节点联盟链支付实验

这是用于架构师考试知识点学习的最小实现，不是生产级区块链。

## 覆盖考点

- 分布式存储：三个 Docker volume 中各有一份 SQLite 区块账本。
- 密码学：SHA-256 串联区块，Ed25519 对交易签名。
- 共识机制：三个节点多数表决；node3 被设置为模拟拜占庭节点并故意投反对票。
- 智能合约：`PaymentContract` 检查联盟成员、签名、余额、正整数金额和 nonce。

## 运行

每次从全新的创世区块开始：

```bash
docker compose down -v
docker compose up -d --build
python3 -m pip install -r requirements.txt
python3 demo.py
```

查看各节点状态：

```bash
curl http://127.0.0.1:8001/state
curl http://127.0.0.1:8002/state
curl http://127.0.0.1:8003/state
```

查看日志和停止环境：

```bash
docker compose logs -f
docker compose down
```
