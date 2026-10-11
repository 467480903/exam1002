# 滤波与卡尔曼滤波学习示例

## 1. 什么是滤波？

传感器读数通常包含噪声。例如真实温度是 `20°C`，传感器可能依次读到
`19.7、20.4、19.9...`。滤波就是从带噪观测中估计更接近真实状态的值。

- **滑动平均**：取最近 N 个观测的平均值。简单，但会产生滞后。
- **一阶低通**：`结果 = α × 新观测 + (1-α) × 上次结果`。α 越小越平滑，滞后也越明显。
- **卡尔曼滤波**：同时考虑“模型预测”和“传感器观测各有多可信”，动态决定更相信哪一个。

## 2. 卡尔曼滤波的核心思想

卡尔曼滤波不断重复两个阶段：

1. **预测**：根据上一时刻的状态和运动模型预测当前状态，同时承认预测会增加不确定性。
2. **更新**：收到传感器观测后，用卡尔曼增益融合预测与观测，并降低不确定性。

一维情况下，主要公式为：

```text
预测状态: x_pred = x
预测方差: P_pred = P + Q
卡尔曼增益: K = P_pred / (P_pred + R)
状态更新: x = x_pred + K * (z - x_pred)
方差更新: P = (1 - K) * P_pred
```

其中：

- `x`：估计值；`z`：传感器观测值。
- `P`：当前估计的不确定性（方差）。
- `Q`：过程噪声，越大表示越不相信运动模型。
- `R`：测量噪声，越大表示越不相信传感器。
- `K`：卡尔曼增益，接近 1 时更相信观测，接近 0 时更相信预测。

经典卡尔曼滤波适合线性系统和近似高斯噪声；非线性系统常使用 EKF、UKF 等变体。

## 3. 示例目录

```text
filter_examples/
├── python/
│   ├── basic_filters.py       # 滑动平均和一阶低通
│   ├── kalman_1d.py           # 一维静态量估计
│   └── kalman_position.py     # 二维状态：位置和速度
└── cpp/
    ├── basic_filters.cpp
    ├── kalman_1d.cpp
    └── kalman_position.cpp
```

所有程序都会打印“真实值、带噪观测、滤波结果”，无需第三方依赖。

## 4. 运行 Python 示例

在本目录执行：

```bash
python3 python/basic_filters.py
python3 python/kalman_1d.py
python3 python/kalman_position.py
```

## 5. 编译和运行 C++ 示例

```bash
cmake -S cpp -B build
cmake --build build
./build/basic_filters
./build/kalman_1d
./build/kalman_position
```

没有 CMake 时也可以直接编译，例如：

```bash
g++ -std=c++17 -O2 cpp/kalman_1d.cpp -o /tmp/kalman_1d
/tmp/kalman_1d
```

## 6. 建议的学习顺序

先运行 `basic_filters`，观察平滑效果和滞后；再修改 `kalman_1d` 的 `Q` 和 `R`；
最后阅读 `kalman_position`，理解卡尔曼滤波如何利用“位置 = 原位置 + 速度 × 时间”这一模型，
从单一的位置观测同时估计位置和速度。

