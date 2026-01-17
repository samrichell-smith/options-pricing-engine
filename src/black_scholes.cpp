#include "black_scholes.hpp"

#include <cmath>

namespace {

/// Standard normal CDF via the complementary error function: N(x) = erfc(-x/√2) / 2.
inline double norm_cdf(double x) { return std::erfc(-x / std::sqrt(2.0)) / 2.0; }

/// Standard normal PDF.
inline double norm_pdf(double x) {
    constexpr double INV_SQRT_2PI = 0.3989422804014327; // 1 / sqrt(2π)
    return INV_SQRT_2PI * std::exp(-0.5 * x * x);
}

/// d1: log-moneyness adjusted for risk-free drift and half-variance; drives delta.
inline double d1(double S, double K, double r, double sigma, double T) {
    return (std::log(S / K) + (r + 0.5 * sigma * sigma) * T) / (sigma * std::sqrt(T));
}

/// d2: d1 minus one standard deviation; risk-neutral probability the option expires ITM.
inline double d2(double d1_val, double sigma, double T) {
    return d1_val - sigma * std::sqrt(T);
}

} // namespace

double price_option(double S, double K, double r, double sigma, double T, OptionType type) {
    const double d1v  = d1(S, K, r, sigma, T);
    const double d2v  = d2(d1v, sigma, T);
    const double disc = std::exp(-r * T);

    if (type == OptionType::CALL) {
        return S * norm_cdf(d1v) - K * disc * norm_cdf(d2v);
    } else {
        return K * disc * norm_cdf(-d2v) - S * norm_cdf(-d1v);
    }
}

Greeks compute_greeks(double S, double K, double r, double sigma, double T, OptionType type) {
    const double d1v   = d1(S, K, r, sigma, T);
    const double d2v   = d2(d1v, sigma, T);
    const double sqrtT = std::sqrt(T);
    const double disc  = std::exp(-r * T);
    const double npd1  = norm_pdf(d1v); // N'(d1): shared by gamma and vega

    Greeks g{};

    // Delta: slope of option price w.r.t. spot
    if (type == OptionType::CALL) {
        g.delta = norm_cdf(d1v);
    } else {
        g.delta = norm_cdf(d1v) - 1.0; // equivalent to -N(-d1)
    }

    // Gamma: identical for calls and puts by put-call parity
    g.gamma = npd1 / (S * sigma * sqrtT);

    // Vega: scaled per 1% absolute vol move (divide textbook vega by 100)
    g.vega = S * npd1 * sqrtT / 100.0;

    // Theta: per calendar day (divide annual rate by 365)
    const double common_term = -(S * npd1 * sigma) / (2.0 * sqrtT);
    if (type == OptionType::CALL) {
        g.theta = (common_term - r * K * disc * norm_cdf(d2v)) / 365.0;
    } else {
        g.theta = (common_term + r * K * disc * norm_cdf(-d2v)) / 365.0;
    }

    return g;
}
