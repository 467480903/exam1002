#include <deque>
#include <iomanip>
#include <iostream>
#include <numeric>
#include <random>
#include <stdexcept>

class MovingAverage {
public:
    explicit MovingAverage(std::size_t window_size) : window_size_(window_size) {
        if (window_size == 0) throw std::invalid_argument("window_size must be positive");
    }

    double update(double measurement) {
        values_.push_back(measurement);
        if (values_.size() > window_size_) values_.pop_front();
        return std::accumulate(values_.begin(), values_.end(), 0.0) / values_.size();
    }

private:
    std::size_t window_size_;
    std::deque<double> values_;
};

class LowPassFilter {
public:
    explicit LowPassFilter(double alpha) : alpha_(alpha) {
        if (alpha <= 0.0 || alpha > 1.0) throw std::invalid_argument("alpha must be in (0, 1]");
    }

    double update(double measurement) {
        if (!initialized_) {
            value_ = measurement;
            initialized_ = true;
        } else {
            value_ = alpha_ * measurement + (1.0 - alpha_) * value_;
        }
        return value_;
    }

private:
    double alpha_;
    double value_ = 0.0;
    bool initialized_ = false;
};

int main() {
    std::mt19937 rng(42);
    std::normal_distribution<double> noise(0.0, 1.2);
    MovingAverage moving_average(5);
    LowPassFilter low_pass(0.25);

    std::cout << "index true measurement moving_avg low_pass\n" << std::fixed << std::setprecision(2);
    for (int i = 0; i < 20; ++i) {
        const double truth = i < 10 ? 20.0 : 25.0;
        const double measurement = truth + noise(rng);
        std::cout << std::setw(2) << i << " " << std::setw(5) << truth << " "
                  << std::setw(11) << measurement << " " << std::setw(10)
                  << moving_average.update(measurement) << " " << std::setw(8)
                  << low_pass.update(measurement) << '\n';
    }
}

