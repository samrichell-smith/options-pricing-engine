"""
Newton-Raphson implied volatility solver.

Vega convention:
    The C++ compute_greeks() returns vega per 1% vol move (textbook vega / 100).
    The NR update needs dV/dσ (textbook vega), so we multiply by 100 before dividing.
"""

import options_pricer as op


def implied_vol(
    market_price: float,
    S: float,
    K: float,
    r: float,
    T: float,
    option_type: op.OptionType = op.OptionType.CALL,
    tol: float = 1e-6,
    max_iter: int = 100,
) -> float:
    """
    Compute the implied volatility of a European option via Newton-Raphson.

    Parameters
    ----------
    market_price : float
        Observed mid-market price of the option.
    S, K, r, T   : float
        Spot, strike, risk-free rate, time to expiry (years).
    option_type   : OptionType
        CALL (default) or PUT.
    tol           : float
        Convergence tolerance on |BS_price - market_price|.
    max_iter      : int
        Maximum iterations before raising ValueError.

    Returns
    -------
    float
        Implied volatility as a decimal (e.g. 0.20 for 20%).
    """
    SIGMA_MIN = 1e-6
    SIGMA_MAX = 10.0

    sigma = 0.20  # initial guess: 20% vol works well for equities

    for i in range(max_iter):
        bs_price = op.price_option(S=S, K=K, r=r, sigma=sigma, T=T, option_type=option_type)
        diff = bs_price - market_price

        if abs(diff) < tol:
            return sigma

        greeks = op.compute_greeks(S=S, K=K, r=r, sigma=sigma, T=T, option_type=option_type)

        # greeks.vega is per 1% vol move; multiply by 100 to get actual dV/dσ
        dv_dsigma = greeks.vega * 100.0

        if abs(dv_dsigma) < 1e-14:
            raise ValueError(
                f"Newton-Raphson stalled: vega ≈ 0 at iteration {i} "
                f"(sigma={sigma:.6f}). Option is likely deep OTM near expiry."
            )

        # Newton-Raphson step: sigma_new = sigma - f(sigma) / f'(sigma)
        sigma -= diff / dv_dsigma

        # Clamp to a valid volatility range to prevent divergence
        sigma = max(SIGMA_MIN, min(SIGMA_MAX, sigma))

    raise ValueError(
        f"Implied vol did not converge after {max_iter} iterations. "
        f"Final sigma={sigma:.6f}, |price diff|={abs(diff):.2e}. "
        f"Check market_price={market_price:.4f} is within no-arbitrage bounds "
        f"(S={S:.2f}, K={K:.2f}, T={T:.4f})."
    )


if __name__ == "__main__":
    # Round-trip check: recover sigma=0.20 from a BS-computed price
    S, K, r, T = 100.0, 100.0, 0.05, 1.0
    true_sigma = 0.20
    reference_price = op.price_option(S=S, K=K, r=r, sigma=true_sigma, T=T,
                                      option_type=op.OptionType.CALL)
    recovered = implied_vol(reference_price, S=S, K=K, r=r, T=T)
    print(f"Target sigma : {true_sigma:.6f}")
    print(f"Recovered IV : {recovered:.6f}")
    print(f"Error        : {abs(recovered - true_sigma):.2e}")
