#include <iomanip>
#include <iostream>
#include <random>

class KalmanFilter1D {
public:
    KalmanFilter1D(double initial_value, double initial_uncertainty,
                   double process_variance, double measurement_variance)
        : x_(initial_value), p_(initial_uncertainty), q_(process_variance),
          r_(measurement_variance) {}

    double update(double measurement) {
        const double predicted_x = x_;
        const double predicted_p = p_ + q_;              // 预测
        gain_ = predicted_p / (predicted_p + r_);        // 卡尔曼增益
        x_ = predicted_x + gain_ * (measurement - predicted_x);
        p_ = (1.0 - gain_) * predicted_p;
        return x_;
    }

    double gain() const { return gain_; }

private:
    double x_, p_, q_, r_;
    double gain_ = 0.0;
};

int main() {
    std::mt19937 rng(42);
    std::normal_distribution<double> noise(0.0, 2.0);
    constexpr double truth = 23.0;
    KalmanFilter1D filter(18.0, 10.0, 0.05, 4.0);

    std::cout << "index true measurement estimate gain\n" << std::fixed << std::setprecision(2);
    for (int i = 0; i < 20; ++i) {
        const double measurement = truth + noise(rng);
        const double estimate = filter.update(measurement);
        std::cout << std::setw(2) << i << " " << std::setw(5) << truth << " "
                  << std::setw(11) << measurement << " " << std::setw(8)
                  << estimate << " " << std::setprecision(3) << filter.gain()
                  << std::setprecision(2) << '\n';
    }
}

