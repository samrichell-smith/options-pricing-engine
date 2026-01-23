"""
Sanity check: prices one contract and prints price + Greeks.
Run from the python/ directory after building the C++ module.
"""

import options_pricer as op

S, K, r, sigma, T = 100.0, 105.0, 0.05, 0.20, 0.5
option_type = op.OptionType.CALL

price  = op.price_option(S=S, K=K, r=r, sigma=sigma, T=T, option_type=option_type)
greeks = op.compute_greeks(S=S, K=K, r=r, sigma=sigma, T=T, option_type=option_type)

print(f"Contract : S={S}, K={K}, r={r}, sigma={sigma}, T={T} yr  [CALL]")
print()
print(f"{'Metric':<10} {'Value':>12}  {'Notes'}")
print("-" * 52)
print(f"{'Price':<10} {price:>12.4f}")
print(f"{'Delta':<10} {greeks.delta:>12.4f}  dV/dS")
print(f"{'Gamma':<10} {greeks.gamma:>12.4f}  d²V/dS²")
print(f"{'Vega':<10} {greeks.vega:>12.4f}  per 1% vol move")
print(f"{'Theta':<10} {greeks.theta:>12.4f}  per calendar day")
