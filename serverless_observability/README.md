# 充电公司 Serverless 与可观测性实验

该项目根据软考系统架构设计师“云原生 Web 系统”材料题建立一个可运行场景。

业务背景：充电公司平时流量较低，但固定时段和营销活动会出现短时流量洪峰。实验使用一个轻量运行时模拟 Serverless/FaaS 的按需启动、自动扩缩容和缩容到零，并展示日志、指标、链路追踪如何协同排障。

> 这是教学模拟器，不是一个生产级 Serverless 平台。真实平台可选 AWS Lambda、Azure Functions、阿里云函数计算、腾讯云云函数、Knative 或 OpenFaaS。

## 一、运行实验

程序只使用 Python 标准库，可以直接运行：

```bash
cd /home/wxf/exam1002/serverless_observability
python3 app.py
```

另开一个终端制造流量洪峰：

```bash
cd /home/wxf/exam1002/serverless_observability
python3 load_test.py
```

也可以使用 Docker：

```bash
docker compose up -d --build
python3 load_test.py
docker compose logs -f
```

停止环境：

```bash
docker compose down
```

删除容器和实验数据：

```bash
docker compose down -v
```

## 二、场景架构

```text
移动端/活动流量
       │
       ▼
   API Gateway                  ← 记录入口 Span、传递 Trace ID
       │
       ├── promotion-function   ← 无状态、按并发扩容、自动重试
       │
       └── payment-function     ← 使用 request_id 保证幂等
                    │
                    ▼
             托管状态服务（本实验用 SQLite 模拟）

失败事件 ──重试3次──→ Dead Letter Queue

运行过程同时产生：
├── application.jsonl   结构化日志
├── /metrics            指标
└── traces.jsonl        调用链 Span
```

另外，`deployment_controller.py` 与 `infra/` 用来演示不可变基础设施和声明式 API。

## 三、你会观察到什么

### 1. 冷启动

初始函数实例数为 0。第一次请求到达时，运行时创建实例并模拟 350ms 的启动开销：

```json
{
  "cold_start": true,
  "instance": 1
}
```

冷启动来自运行环境初始化、加载代码和建立外部连接。真实系统可通过减少依赖、缩小制品、预置并发等方法优化。

### 2. 弹性扩容

`load_test.py` 同时发送 24 个请求。模拟器发现现有实例无法承载并发后，逐步扩容，最大实例数由 `MAX_INSTANCES` 控制。

生产平台还会考虑：

- 每个实例允许的并发数；
- 区域账户并发配额；
- 下游数据库连接上限；
- 扩容速度和突发并发额度；
- 最大实例数，防止异常流量导致费用失控。

### 3. 缩容到零

空闲 8 秒后，实例数降到配置的预置实例数。默认预置数为 0，因此会缩容到零；这样平时低流量时不持续占用计算资源，体现 Serverless 的按使用量计费思想。

### 4. 无状态与外部状态

函数实例可能随时创建或销毁，所以业务状态不能只存在实例内存中。本实验把扣费记录存入外部 SQLite；真实系统应使用云数据库、对象存储、缓存或消息服务。

### 5. 幂等

事件系统通常采用“至少一次”投递，请求可能重复。扣费接口使用唯一 `request_id`：

```text
第一次：charged
第二次：already_processed
```

这可以防止同一个充电订单被重复扣费。幂等是 Serverless 和事件驱动架构的重要考点。

### 6. 重试和死信队列

`fail=1` 会模拟优惠规则服务不可用。运行时重试三次，仍然失败就把事件写入 `dead_letter_queue.jsonl`，用于后续人工检查或补偿处理。

## 四、三大可观测性支柱

### 日志 Logging

文件：`runtime_data/application.jsonl`，Docker 模式下同时可用：

```bash
docker compose logs -f
```

日志使用 JSON 结构，包含时间、级别、服务、函数、实例和 `trace_id`。它回答：**具体发生了什么，异常原因是什么？**

### 指标 Metrics

```bash
curl http://localhost:8080/metrics
```

包括：

- `requests_total`：请求总数；
- `requests_failed_total`：失败请求数；
- `cold_starts_total`：冷启动次数；
- `scale_out_total`：扩容次数；
- `retries_total`：重试次数；
- `dlq_messages_total`：死信数量；
- `instances`：当前实例数；
- `in_flight`：正在执行的请求数。

指标回答：**系统是否异常、何时异常、影响范围多大？**

生产系统可使用 OpenTelemetry、Prometheus 和 Grafana 采集、展示和告警。

### 链路追踪 Tracing

文件：`runtime_data/traces.jsonl`。一次扣费请求大致形成：

```text
api-gateway: invoke:payment-function
└── payment-function: charge
    └── managed-database: insert-payment
```

所有 Span 共享一个 `trace_id`，并通过 `parent_span_id` 形成父子关系。链路回答：**请求经过哪里，慢在哪里，失败在哪里？**

生产系统通常使用 OpenTelemetry 采集，使用 Jaeger、Tempo、SkyWalking 等保存和查看链路。

## 五、故障排查闭环

假设优惠活动期间用户反馈领取失败：

1. 从指标发现 `requests_failed_total` 和延迟升高；
2. 找到一个失败响应中的 `trace_id`；
3. 用 `trace_id` 检索 `traces.jsonl`，定位失败的函数或下游调用；
4. 用同一个 `trace_id` 检索 `application.jsonl`，查看重试次数和异常信息；
5. 检查 `dead_letter_queue.jsonl` 是否有待补偿事件；
6. 修复后再次观察错误率、延迟和死信数量。

速记：**指标发现问题，链路定位位置，日志分析原因。**

## 六、Serverless 的特点

Serverless 不是“没有服务器”，而是服务器、运行时、扩缩容和基础设施运维主要由平台负责。

| 特性 | 含义 |
|---|---|
| 无需管理服务器 | 用户主要提交函数或容器代码 |
| 事件驱动 | HTTP、消息、定时器、文件上传等事件触发 |
| 自动扩缩容 | 根据请求和事件数量调整实例 |
| 按使用量计费 | 通常按调用次数和执行资源时间计费 |
| 无状态计算 | 状态放在外部托管服务中 |
| 短生命周期 | 实例可能随时创建、复用或销毁 |

## 七、优点和局限

优点：

- 适合流量潮汐明显的业务；
- 运维负担较低；
- 能快速交付独立功能；
- 天然适合事件驱动和异步任务；
- 空闲时可以缩容，降低部分资源成本。

局限：

- 冷启动会增加延迟；
- 执行时间、内存和并发可能受平台限制；
- 依赖云厂商事件和运行时，可能产生厂商绑定；
- 本地调试、分布式排错和成本预测更复杂；
- 突然扩容可能压垮数据库等非弹性下游；
- 不适合所有长时间运行、高状态或极低延迟任务。

## 八、Serverless 与容器、微服务的关系

- **微服务**是一种业务和软件架构拆分方式；
- **容器**是一种应用打包和隔离技术；
- **Serverless**是一种云服务使用和运维模型；
- 函数可以实现一个微服务，但微服务不一定是函数；
- Serverless 平台底层也可能使用容器和 Kubernetes。

因此三者不是互斥的同类概念。

## 九、对应软考答题要点

面对本题场景，可写：

1. 使用 API 网关统一鉴权、限流和路由；
2. 将营销、计费等功能拆为无状态函数或微服务；
3. 固定高峰前可使用预置并发，突发流量由自动扩容承接；
4. 业务状态保存在外部数据库和缓存中；
5. 消息处理采用幂等键、重试、死信队列和补偿机制；
6. 通过最大实例数、数据库连接池和背压保护下游；
7. 使用日志、指标和链路追踪建设可观测性；
8. 故障排查遵循“指标发现、链路定位、日志定因”；
9. 对关键数据采用事务数据库，不把临时函数实例作为状态载体；
10. 评估冷启动、厂商绑定、执行限制和成本风险。

## 十、冷启动：原因、观测和优化

### 1. 冷启动为什么发生

函数没有可复用的热实例时，平台通常需要依次完成：

```text
收到事件
  ↓
调度节点、分配容器或微虚拟机
  ↓
准备网络、挂载文件和安全策略
  ↓
启动语言运行时（JVM/Python/Node 等）
  ↓
下载或解压函数制品、加载依赖
  ↓
执行用户初始化代码、建立外部连接
  ↓
执行本次请求
```

导致冷启动变慢的因素包括：制品和依赖过大、JVM 等运行时启动较慢、全局初始化复杂、VPC 网络准备、首次建立数据库连接以及短时间快速扩容出大量新实例。

本实验把 350ms 冷启动拆成三个可观测 Span：

```text
serverless-platform: cold-start
├── allocate-sandbox       资源、网络和隔离环境
├── load-runtime           加载语言运行时
└── initialize-code        加载依赖和用户初始化
```

执行流量实验后，可以查看：

```bash
grep 'cold-start\|allocate-sandbox\|load-runtime\|initialize-code' \
  runtime_data/traces.jsonl
curl http://localhost:8080/metrics
```

指标 `cold_starts_total` 统计次数，`cold_start_duration_ms_sum` 累计冷启动耗时。

### 2. 优化方案：预置并发

在已知居民区早晚高峰、商圈白天高峰或营销活动即将开始时，预先保持热实例：

```bash
PROVISIONED_INSTANCES=1 python3 app.py
```

Docker 中修改 `compose.yaml`：

```yaml
environment:
  - PROVISIONED_INSTANCES=1
```

然后重新创建容器：

```bash
docker compose up -d --build --force-recreate
```

首次请求将直接使用热实例，避免从零启动。代价是即使没有请求，预置实例也会持续占用资源并产生费用。因此可以结合充电业务的潮汐规律，在高峰前定时预热，高峰后降低预置并发。

其他优化方法：

- 减少依赖和镜像/函数包大小；
- 避免在全局初始化阶段执行不必要工作；
- 复用数据库、HTTP 客户端和连接池；
- 选择启动更快的运行时，或使用 AOT/快照技术；
- 避免不必要的 VPC 接入；
- 将低延迟核心接口与可异步执行的任务分开；
- 持续监控冷启动次数、初始化时长和 P95/P99 延迟。

考试可概括为：**冷启动由运行环境和用户代码首次初始化产生；可通过精简制品、优化初始化和预置并发降低延迟。**

## 十一、不可变基础设施

不可变基础设施是指：服务器、容器或函数制品部署后，不再登录实例原地修改软件和配置。需要升级或改配置时，根据新版本镜像重新创建实例，验证成功后切换流量并删除旧实例。

```text
传统可变方式
SSH 登录服务器 → apt/pip 安装 → 修改配置 → 重启
                     ↓
         各服务器状态可能逐渐不一致

不可变方式
构建 image:v2@sha256... → 创建新实例 → 健康检查 → 切换流量 → 删除 v1
```

实验使用镜像摘要表示不可变制品：

```json
{
  "image": "charging-functions:1.0.0",
  "digest": "sha256:1111111111111111111111111111111111111111111111111111111111111111"
}
```

标签可能被误覆盖，而 digest 唯一标识镜像内容。控制器会验证标签和 digest 是否与 `infra/image_registry.json` 一致；同一版本内容被改变时拒绝部署。

运行发布和回滚实验：

```bash
python3 deployment_controller.py demo
```

输出会依次展示：

1. 创建 v1；
2. 重复提交相同状态时不做操作，体现幂等；
3. 发布 v2 时创建新实例、健康检查、切换流量、删除旧实例；
4. 回滚时根据 v1 镜像重新创建资源，而不是修改 v2 实例。

优势：

- 所有实例来自相同镜像，消除手工修改造成的配置漂移；
- 测试、预生产和生产环境使用同一制品，提高环境一致性；
- 部署过程可重复、可审计；
- 回滚只需重新部署旧版本制品；
- 故障实例可以直接替换，减少“雪花服务器”。

## 十二、声明式 API

声明式 API 描述“系统最终应该是什么状态”，而不是逐条说明“怎样修改系统”。

本实验的 [`infra/desired_state.json`](infra/desired_state.json) 描述：

```json
{
  "application": "charging-functions",
  "image": "charging-functions:1.0.0",
  "digest": "sha256:1111111111111111111111111111111111111111111111111111111111111111",
  "replicas": 2,
  "environment": {
    "LOG_LEVEL": "INFO",
    "FEATURE_PROMOTION": "true"
  }
}
```

执行：

```bash
python3 deployment_controller.py reconcile
python3 deployment_controller.py status
```

控制器不断比较：

```text
期望状态 desired state
          │
          ▼
       Reconcile
          │
          ▼
实际状态 actual state
```

如果期望 2 个副本而实际只有 1 个，控制器补建 1 个；如果实例故障只剩 1 个，控制器仍会再次补齐。这正是 Kubernetes Controller/Reconciliation Loop 的核心思想。

传统命令式操作可能是：

```text
登录服务器A → 修改配置 → 重启
登录服务器B → 修改配置 → 重启
```

声明式方式则是：

```text
提交一份期望状态 → 控制器自动让所有环境收敛
```

环境一致性和部署可靠性的优势：

- 声明文件可以进入 Git，接受评审并保留变更历史；
- 重复提交结果一致，具有幂等性；
- 测试和生产可使用同一模板，只改变受控参数；
- 控制器自动纠正实际状态偏差；
- 配合不可变镜像实现可重复发布和快速回滚；
- 减少人工 SSH 操作、漏改和误操作。

考试可概括为：**不可变基础设施通过“替换而非修改”消除配置漂移；声明式 API 描述期望状态，由控制器持续协调实际状态，从而提高环境一致性、部署可重复性和回滚可靠性。**

