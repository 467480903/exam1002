#!/usr/bin/env python3
"""一维卡尔曼滤波：从有噪温度观测中估计真实温度。"""

import random


class KalmanFilter1D:
    def __init__(self, initial_value: float, initial_uncertainty: float,
                 process_variance: float, measurement_variance: float) -> None:
        self.x = initial_value
        self.p = initial_uncertainty
        self.q = process_variance
        self.r = measurement_variance

    def update(self, measurement: float) -> tuple[float, float]:
        # 1. 预测：静态模型认为数值不变，但不确定性增加 Q。
        predicted_x = self.x
        predicted_p = self.p + self.q

        # 2. 更新：K 决定本次更相信预测还是观测。
        kalman_gain = predicted_p / (predicted_p + self.r)
        self.x = predicted_x + kalman_gain * (measurement - predicted_x)
        self.p = (1.0 - kalman_gain) * predicted_p
        return self.x, kalman_gain


def main() -> None:
    rng = random.Random(42)
    true_temperature = 23.0
    measurement_std = 2.0
    kf = KalmanFilter1D(
        initial_value=18.0,
        initial_uncertainty=10.0,
        process_variance=0.05,          # Q：温度本身变化较慢
        measurement_variance=measurement_std ** 2,  # R：传感器噪声方差
    )

    print("序号  真实值    观测值    估计值    K")
    for index in range(20):
        measurement = true_temperature + rng.gauss(0.0, measurement_std)
        estimate, gain = kf.update(measurement)
        print(f"{index:>2}  {true_temperature:>7.2f}  {measurement:>7.2f}  "
              f"{estimate:>7.2f}  {gain:>.3f}")


if __name__ == "__main__":
    main()

