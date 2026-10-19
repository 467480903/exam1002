# 第三方认证学习示例

本项目用两个可以直接运行的 Python 示例，演示第三方认证的两条典型路线：

```text
Kerberos：客户端和服务端共同信任 KDC，KDC 签发票据
PKI：通信双方共同信任 CA，CA 签发数字证书
```

## 1. 目录内容

```text
third_party_auth_demo/
├── kerberos_ticket_demo.py   # KDC、服务票据、过期和重放检测的教学模拟
├── pki_certificate_demo.py   # CA、服务器证书、挑战签名和篡改检测
├── compare_demo.py           # 连续运行两种机制并输出对比结论
├── test_auth_demos.py        # 自动化测试
└── requirements.txt          # PKI 示例使用的第三方库
```

> `kerberos_ticket_demo.py` 是为了讲清原理而编写的简化模拟，不是 Kerberos 协议实现，也不能用于生产环境。真实 Kerberos 还包含 AS、TGS、TGT、会话密钥和完整的网络协议。

## 2. 环境准备

进入目录并创建虚拟环境：

```bash
cd /home/wxf/exam1002/third_party_auth_demo
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

当前系统如果已经安装 `cryptography`，也可以直接运行。

## 3. 运行 Kerberos 票据模拟

```bash
python kerberos_ticket_demo.py
```

程序依次演示：

1. 用户向可信 KDC 证明身份；
2. KDC 为指定服务签发有时效的票据；
3. 服务使用与 KDC 共享的密钥验证票据；
4. 同一票据再次使用时触发重放检测；
5. 被篡改的票据无法通过完整性校验。

简化流程：

```text
Alice ──身份验证──> KDC
Alice <──服务票据── KDC
Alice ──服务票据──> inventory-service
                       │
                       └─ 使用共享密钥验证KDC签名
```

重要角色：

- KDC：Key Distribution Center，密钥分发中心；
- AS：Authentication Server，认证服务器；
- TGS：Ticket Granting Server，票据授予服务器；
- Ticket：KDC签发、供客户端访问服务的票据。

本示例把 AS/TGS 合并在一个 `SimpleKDC` 类中，以减少与主题无关的代码。

## 4. 运行 PKI 证书认证

```bash
python pki_certificate_demo.py
```

程序依次演示：

1. 创建一个教学用根CA；
2. CA为服务器公钥签发数字证书；
3. 客户端使用CA公钥验证服务器证书；
4. 服务器用私钥签署客户端随机挑战；
5. 客户端使用证书内的服务器公钥验证签名；
6. 篡改挑战数据后，签名验证失败。

简化流程：

```text
服务器 ──公钥及身份申请──> CA
服务器 <────数字证书────── CA

客户端 ─────随机挑战─────> 服务器
客户端 <─证书＋挑战签名──── 服务器
   │
   ├─ 使用CA公钥验证证书
   └─ 使用证书内公钥验证挑战签名
```

PKI 中的关键对象：

- CA：Certificate Authority，证书颁发机构；
- 数字证书：把主体身份和公钥绑定起来；
- CA私钥：用于签发证书，必须严格保护；
- 服务器私钥：用于证明服务器确实持有证书对应的私钥；
- 信任锚：客户端预先信任的根CA证书或公钥。

## 5. 连续运行两个示例

```bash
python compare_demo.py
```

运行后观察两种机制的信任差异：

| 项目 | Kerberos | PKI |
|---|---|---|
| 可信第三方 | KDC | CA |
| 认证载体 | 票据 | 数字证书 |
| 主要密码机制 | 对称密钥 | 非对称密钥和数字签名 |
| 身份证明 | KDC确认用户后签发票据 | CA验证主体后签发证书 |
| 服务端验证依据 | 与KDC共享的服务密钥 | 受信任CA的公钥 |
| 常见用途 | 企业内网、域认证、单点登录 | HTTPS、设备证书、跨组织信任 |

记忆口诀：

> Kerberos 找 KDC 拿票；PKI 找 CA 拿证。

## 6. 运行自动化测试

```bash
python -m unittest -v
```

测试覆盖：

- 正常票据可以验证；
- 票据不能重复使用；
- 票据不能交给错误的服务；
- CA签发的证书可以验证；
- 非受信任CA签发的证书不能通过验证；
- 正确挑战签名可以验证；
- 数据被篡改后签名验证失败。

## 7. 示例与生产系统的区别

生产环境不要自行设计认证协议。应使用成熟实现，例如企业Kerberos服务、操作系统域认证、TLS库和受控PKI平台。生产系统还必须考虑：

- 密钥安全存储和轮换；
- 时钟同步；
- 证书吊销和OCSP/CRL；
- 票据与证书的有效期；
- 算法和密钥长度策略；
- 审计日志；
- 高可用和灾难恢复；
- 中间人、重放、降级及侧信道攻击。

本项目的目标是帮助理解软考中的概念对应关系，而不是提供生产认证代码。
