#include "../src/batch_pricer.hpp"

#include <chrono>
#include <cstdio>
#include <random>
#include <vector>

int main() {
    constexpr std::size_t N = 1'000'000;

    // Reproducible random contracts using a seeded Mersenne Twister
    std::mt19937 rng(42);
    std::uniform_real_distribution<double> spot_dist(80.0, 120.0);
    std::uniform_real_distribution<double> strike_dist(70.0, 130.0);
    std::uniform_real_distribution<double> vol_dist(0.10, 0.50);
    std::uniform_real_distribution<double> T_dist(0.10, 2.00);
    const double r = 0.05;

    std::vector<Contract> contracts;
    contracts.reserve(N);

    for (std::size_t i = 0; i < N; ++i) {
        const OptionType type = (i % 2 == 0) ? OptionType::CALL : OptionType::PUT;
        contracts.push_back({spot_dist(rng), strike_dist(rng), r, vol_dist(rng), T_dist(rng), type});
    }

    // Time only the pricing step, not data generation
    const auto t0     = std::chrono::high_resolution_clock::now();
    const auto prices = price_batch(contracts);
    const auto t1     = std::chrono::high_resolution_clock::now();

    const double ms               = std::chrono::duration<double, std::milli>(t1 - t0).count();
    const double contracts_per_sec = static_cast<double>(N) / (ms / 1000.0);

    std::printf("Contracts priced : %zu\n", N);
    std::printf("Total time       : %.2f ms\n", ms);
    std::printf("Throughput       : %.0f contracts/sec\n", contracts_per_sec);

    (void)prices; // suppress unused-variable warning
    return 0;
}
