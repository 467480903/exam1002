# Vue + Flask + SQLite 登录示例

演示账号：`admin`，密码：`password123`。

## 安装

```bash
cd web_test/frontend
npm install
npx playwright install chromium
```

Python 环境已安装 Flask 时无需额外操作；否则运行：

```bash
python3 -m pip install -r web_test/backend/requirements.txt
```

## 启动

分别打开两个终端：

```bash
python3 web_test/backend/app.py
```

```bash
cd web_test/frontend
npm run dev
```

访问 <http://127.0.0.1:5173>。

## 浏览器自动测试

```bash
cd web_test/frontend
npm run test:e2e
```

测试工具会自动启动前后端服务，并模拟输入账号、密码和点击登录按钮。
