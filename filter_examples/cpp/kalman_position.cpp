#include <iomanip>
#include <iostream>
#include <random>
#include <utility>

class PositionVelocityKalmanFilter {
public:
    PositionVelocityKalmanFilter(double dt, double acceleration_variance,
                                 double measurement_variance)
        : dt_(dt), q_(acceleration_variance), r_(measurement_variance) {}

    std::pair<double, double> update(double measured_position) {
        // 预测状态：F = [[1, dt], [0, 1]]。
        position_ += dt_ * velocity_;

        // P = F P F^T + Q。
        const double old00 = p00_, old01 = p01_, old10 = p10_, old11 = p11_;
        const double q00 = 0.25 * dt_ * dt_ * dt_ * dt_ * q_;
        const double q01 = 0.5 * dt_ * dt_ * dt_ * q_;
        const double q11 = dt_ * dt_ * q_;
        p00_ = old00 + dt_ * (old10 + old01) + dt_ * dt_ * old11 + q00;
        p01_ = old01 + dt_ * old11 + q01;
        p10_ = old10 + dt_ * old11 + q01;
        p11_ = old11 + q11;

        // 用位置观测更新，H = [1, 0]。
        const double innovation = measured_position - position_;
        const double innovation_variance = p00_ + r_;
        const double k0 = p00_ / innovation_variance;
        const double k1 = p10_ / innovation_variance;
        position_ += k0 * innovation;
        velocity_ += k1 * innovation;

        const double a = p00_, b = p01_, c = p10_, d = p11_;
        p00_ = (1.0 - k0) * a;
        p01_ = (1.0 - k0) * b;
        p10_ = c - k1 * a;
        p11_ = d - k1 * b;
        return {position_, velocity_};
    }

private:
    double dt_, q_, r_;
    double position_ = 0.0, velocity_ = 0.0;
    double p00_ = 10.0, p01_ = 0.0, p10_ = 0.0, p11_ = 10.0;
};

int main() {
    std::mt19937 rng(42);
    std::normal_distribution<double> noise(0.0, 3.0);
    constexpr double dt = 1.0, true_velocity = 2.0;
    PositionVelocityKalmanFilter filter(dt, 0.1, 9.0);

    std::cout << "time true_pos measured_pos estimated_pos estimated_vel\n"
              << std::fixed << std::setprecision(2);
    for (int step = 1; step <= 20; ++step) {
        const double true_position = true_velocity * step * dt;
        const double measurement = true_position + noise(rng);
        const auto [position, velocity] = filter.update(measurement);
        std::cout << std::setw(2) << step << " " << std::setw(8) << true_position
                  << " " << std::setw(12) << measurement << " " << std::setw(13)
                  << position << " " << std::setw(13) << velocity << '\n';
    }
}
