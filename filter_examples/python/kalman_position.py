#!/usr/bin/env python3
"""常速度卡尔曼滤波：用带噪位置观测估计位置和速度。"""

import random


class PositionVelocityKalmanFilter:
    def __init__(self, dt: float, acceleration_variance: float,
                 measurement_variance: float) -> None:
        self.dt = dt
        self.q = acceleration_variance
        self.r = measurement_variance
        self.position = 0.0
        self.velocity = 0.0
        # 状态协方差矩阵 P
        self.p00, self.p01 = 10.0, 0.0
        self.p10, self.p11 = 0.0, 10.0

    def update(self, measured_position: float) -> tuple[float, float]:
        dt = self.dt

        # 预测状态，状态转移矩阵 F = [[1, dt], [0, 1]]。
        self.position += dt * self.velocity

        # P = F P F^T + Q；Q 来自未建模的随机加速度。
        q00 = 0.25 * dt ** 4 * self.q
        q01 = 0.5 * dt ** 3 * self.q
        q11 = dt ** 2 * self.q
        old00, old01, old10, old11 = self.p00, self.p01, self.p10, self.p11
        self.p00 = old00 + dt * (old10 + old01) + dt * dt * old11 + q00
        self.p01 = old01 + dt * old11 + q01
        self.p10 = old10 + dt * old11 + q01
        self.p11 = old11 + q11

        # 位置观测矩阵 H = [1, 0]。
        innovation = measured_position - self.position
        innovation_variance = self.p00 + self.r
        k0 = self.p00 / innovation_variance
        k1 = self.p10 / innovation_variance
        self.position += k0 * innovation
        self.velocity += k1 * innovation

        # P = (I - K H) P。先保存，避免原地更新相互干扰。
        p00, p01, p10, p11 = self.p00, self.p01, self.p10, self.p11
        self.p00 = (1.0 - k0) * p00
        self.p01 = (1.0 - k0) * p01
        self.p10 = p10 - k1 * p00
        self.p11 = p11 - k1 * p01
        return self.position, self.velocity


def main() -> None:
    rng = random.Random(42)
    dt, true_velocity, measurement_std = 1.0, 2.0, 3.0
    kf = PositionVelocityKalmanFilter(dt, acceleration_variance=0.1,
                                      measurement_variance=measurement_std ** 2)

    print("时间  真实位置  观测位置  估计位置  估计速度")
    for step in range(1, 21):
        true_position = true_velocity * step * dt
        measurement = true_position + rng.gauss(0.0, measurement_std)
        position, velocity = kf.update(measurement)
        print(f"{step:>2}s  {true_position:>8.2f}  {measurement:>8.2f}  "
              f"{position:>8.2f}  {velocity:>8.2f}")


if __name__ == "__main__":
    main()

