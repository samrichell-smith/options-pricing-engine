#pragma once

/// Option type: European call or put.
enum class OptionType { CALL, PUT };

/// Sensitivities of an option's price to its inputs.
struct Greeks {
    double delta; ///< dV/dS; positive [0,1] for calls, negative [-1,0] for puts
    double gamma; ///< d²V/dS²; always positive, peaks near ATM
    double vega;  ///< dV/dσ per 1% vol move; always positive for long options
    double theta; ///< dV/dT per calendar day; usually negative (time decay hurts longs)
};

/// Black-Scholes price of a European option.
/// @param S     Spot price
/// @param K     Strike price
/// @param r     Continuously compounded risk-free rate (e.g. 0.05)
/// @param sigma Volatility (e.g. 0.20)
/// @param T     Time to expiry in years
/// @param type  CALL or PUT
double price_option(double S, double K, double r, double sigma, double T, OptionType type);

/// Analytical Black-Scholes Greeks for a European option.
/// Same parameter conventions as price_option.
Greeks compute_greeks(double S, double K, double r, double sigma, double T, OptionType type);
