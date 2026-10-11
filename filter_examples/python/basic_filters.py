#!/usr/bin/env python3
"""滑动平均与一阶低通滤波：仅使用 Python 标准库。"""

from collections import deque
import random


class MovingAverage:
    def __init__(self, window_size: int) -> None:
        if window_size <= 0:
            raise ValueError("window_size 必须大于 0")
        self.values: deque[float] = deque(maxlen=window_size)

    def update(self, measurement: float) -> float:
        self.values.append(measurement)
        return sum(self.values) / len(self.values)


class LowPassFilter:
    def __init__(self, alpha: float) -> None:
        if not 0.0 < alpha <= 1.0:
            raise ValueError("alpha 必须在 (0, 1] 范围内")
        self.alpha = alpha
        self.value: float | None = None

    def update(self, measurement: float) -> float:
        if self.value is None:
            self.value = measurement
        else:
            self.value = self.alpha * measurement + (1.0 - self.alpha) * self.value
        return self.value


def main() -> None:
    rng = random.Random(42)  # 固定种子，使结果可复现
    moving_average = MovingAverage(window_size=5)
    low_pass = LowPassFilter(alpha=0.25)

    print("序号  真实值    观测值    滑动平均  低通结果")
    for index in range(20):
        true_value = 20.0 if index < 10 else 25.0  # 第 10 次发生阶跃变化
        measurement = true_value + rng.gauss(0.0, 1.2)
        average = moving_average.update(measurement)
        filtered = low_pass.update(measurement)
        print(f"{index:>2}  {true_value:>7.2f}  {measurement:>7.2f}  "
              f"{average:>8.2f}  {filtered:>8.2f}")


if __name__ == "__main__":
    main()

