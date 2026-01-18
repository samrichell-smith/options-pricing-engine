#pragma once

#include "black_scholes.hpp"

#include <vector>

/// All parameters needed to price a single option contract.
struct Contract {
    double S;           ///< Spot price of the underlying
    double K;           ///< Strike price
    double r;           ///< Risk-free rate
    double sigma;       ///< Volatility
    double T;           ///< Time to expiry in years
    OptionType option_type; ///< CALL or PUT
};

/// Price a batch of contracts using the Black-Scholes formula.
/// Returns prices in the same order as the input vector.
std::vector<double> price_batch(const std::vector<Contract>& contracts);
