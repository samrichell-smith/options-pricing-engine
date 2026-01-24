"""
Plots the four Black-Scholes Greeks (Delta, Gamma, Vega, Theta) against spot price
for a European call and put with fixed parameters.

No market data required — fully deterministic.

Usage:
    python3 greeks_viz.py
"""

import numpy as np
import matplotlib.pyplot as plt
import sys
import os

# Allow running from the python/ directory directly
sys.path.insert(0, os.path.dirname(__file__))
import options_pricer as op

# Fixed parameters
K     = 100.0
r     = 0.05
sigma = 0.20
T     = 0.5

S_range = np.linspace(60, 140, 500)

# Accumulate Greeks for each spot price
call_delta, put_delta   = [], []
gamma_vals              = []   # identical for call and put
vega_vals               = []   # identical for call and put
call_theta, put_theta   = [], []

for s in S_range:
    cg = op.compute_greeks(S=s, K=K, r=r, sigma=sigma, T=T,
                           option_type=op.OptionType.CALL)
    pg = op.compute_greeks(S=s, K=K, r=r, sigma=sigma, T=T,
                           option_type=op.OptionType.PUT)

    call_delta.append(cg.delta)
    put_delta.append(pg.delta)

    gamma_vals.append(cg.gamma)      # same for both
    vega_vals.append(cg.vega * 100)  # convert to textbook vega (per unit σ)

    # Theta: C++ returns annualised; divide by 365 for per-calendar-day
    call_theta.append(cg.theta / 365.0)
    put_theta.append(pg.theta / 365.0)

call_delta  = np.array(call_delta)
put_delta   = np.array(put_delta)
gamma_vals  = np.array(gamma_vals)
vega_vals   = np.array(vega_vals)
call_theta  = np.array(call_theta)
put_theta   = np.array(put_theta)

ATM_LINE_KW = dict(color="grey", linestyle="--", linewidth=1.2,
                   label="ATM (K=100)")

fig, axes = plt.subplots(2, 2, figsize=(12, 8))
fig.suptitle(
    r"Black-Scholes Greeks — $K=100$, $r=5\%$, $\sigma=20\%$, $T=0.5\,\mathrm{yr}$",
    fontsize=14,
)

# --- Delta ---
ax = axes[0, 0]
ax.plot(S_range, call_delta, color="steelblue", label="Call Δ")
ax.plot(S_range, put_delta,  color="tomato",    label="Put Δ")
ax.axvline(K, **ATM_LINE_KW)
ax.set_title("Delta")
ax.set_xlabel("Spot (S)")
ax.set_ylabel("Delta")
ax.legend(fontsize=9)
ax.grid(True, alpha=0.3)

# --- Gamma ---
ax = axes[0, 1]
ax.plot(S_range, gamma_vals, color="mediumseagreen", label="Γ (call = put)")
ax.axvline(K, **ATM_LINE_KW)
ax.set_title("Gamma")
ax.set_xlabel("Spot (S)")
ax.set_ylabel("Gamma")
ax.legend(fontsize=9)
ax.grid(True, alpha=0.3)

# --- Vega ---
ax = axes[1, 0]
ax.plot(S_range, vega_vals, color="mediumpurple", label="Vega (call = put)")
ax.axvline(K, **ATM_LINE_KW)
ax.set_title("Vega")
ax.set_xlabel("Spot (S)")
ax.set_ylabel("Vega (per unit σ)")
ax.legend(fontsize=9)
ax.grid(True, alpha=0.3)

# --- Theta ---
ax = axes[1, 1]
ax.plot(S_range, call_theta, color="steelblue", label="Call Θ")
ax.plot(S_range, put_theta,  color="tomato",    label="Put Θ")
ax.axvline(K, **ATM_LINE_KW)
ax.set_title("Theta (per day)")
ax.set_xlabel("Spot (S)")
ax.set_ylabel("Theta (per calendar day)")
ax.legend(fontsize=9)
ax.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig("greeks_viz.png", dpi=150, bbox_inches="tight")
print("Saved greeks_viz.png")
plt.show()
