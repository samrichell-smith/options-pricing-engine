#include "batch_pricer.hpp"

#include "black_scholes.hpp"

std::vector<double> price_batch(const std::vector<Contract>& contracts) {
    std::vector<double> prices;
    prices.reserve(contracts.size()); // avoid repeated reallocations over 1M+ iterations

    for (const auto& c : contracts) {
        prices.push_back(price_option(c.S, c.K, c.r, c.sigma, c.T, c.option_type));
    }

    return prices;
}
