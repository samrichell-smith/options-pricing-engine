"""
Plots the implied volatility smile for a near-term equity option chain.

Fetches live data from Yahoo Finance, computes IV per strike via Newton-Raphson,
and plots the smile with a horizontal dashed line showing the BS flat-vol assumption.

Usage:
    python volatility_smile.py [--ticker TICKER]
"""

import argparse
import sys
from datetime import datetime, timedelta

import matplotlib.pyplot as plt
import numpy as np
import yfinance as yf

import options_pricer as op
from implied_vol import implied_vol

# Liquidity filters
MAX_SPREAD_RATIO = 0.50  # skip if (ask - bid) / ask > 50%
STRIKE_BAND = 0.20       # only consider strikes within ±20% of spot
RISK_FREE_RATE = 0.05    # approximate risk-free rate


def select_expiry(ticker_obj, target_days: int = 30) -> str:
    """Return the expiry string (YYYY-MM-DD) closest to target_days from today."""
    today = datetime.today().date()
    target = today + timedelta(days=target_days)
    return min(
        ticker_obj.options,
        key=lambda e: abs((datetime.strptime(e, "%Y-%m-%d").date() - target).days),
    )


def compute_smile(chain_df, spot: float, T: float, option_type: op.OptionType):
    """
    For each strike in chain_df, compute the implied volatility from the mid price.

    Filters applied:
    - bid > 0 (active market maker)
    - (ask - bid) / ask <= MAX_SPREAD_RATIO (liquid enough)
    - strike within ±STRIKE_BAND of spot

    Returns (strikes, ivs) as numpy arrays (IV as decimal, e.g. 0.20 for 20%).
    """
    strikes, ivs = [], []

    low  = spot * (1.0 - STRIKE_BAND)
    high = spot * (1.0 + STRIKE_BAND)

    for _, row in chain_df.iterrows():
        strike = float(row["strike"])
        bid    = float(row["bid"])
        ask    = float(row["ask"])

        if bid <= 0 or ask <= 0:
            continue
        if (ask - bid) / ask > MAX_SPREAD_RATIO:
            continue
        if not (low <= strike <= high):
            continue

        mid = (bid + ask) / 2.0

        try:
            iv = implied_vol(
                market_price=mid,
                S=spot,
                K=strike,
                r=RISK_FREE_RATE,
                T=T,
                option_type=option_type,
            )
            strikes.append(strike)
            ivs.append(iv)
        except ValueError:
            # Skip strikes where the IV solver cannot converge
            continue

    return np.array(strikes), np.array(ivs)


def main() -> None:
    parser = argparse.ArgumentParser(description="Plot the implied volatility smile.")
    parser.add_argument("--ticker", default="SPY", help="Underlying ticker (default: SPY)")
    args = parser.parse_args()
    ticker_sym = args.ticker.upper()

    print(f"Fetching data for {ticker_sym}...")
    stock = yf.Ticker(ticker_sym)

    spot = float(stock.fast_info["lastPrice"])
    print(f"Spot: {spot:.2f}")

    expiry = select_expiry(stock)
    today  = datetime.today().date()
    T      = (datetime.strptime(expiry, "%Y-%m-%d").date() - today).days / 365.0
    print(f"Expiry: {expiry}  (T = {T:.4f} yr)")

    chain = stock.option_chain(expiry)

    call_strikes, call_ivs = compute_smile(chain.calls, spot, T, op.OptionType.CALL)
    put_strikes,  put_ivs  = compute_smile(chain.puts,  spot, T, op.OptionType.PUT)

    if len(call_strikes) == 0 and len(put_strikes) == 0:
        print("No valid IV data found after filtering. Check the ticker and market hours.")
        sys.exit(1)

    # Combine for ATM IV interpolation
    all_strikes = np.concatenate([put_strikes, call_strikes])
    all_ivs     = np.concatenate([put_ivs,     call_ivs])
    sort_idx    = np.argsort(all_strikes)
    all_strikes = all_strikes[sort_idx]
    all_ivs     = all_ivs[sort_idx]

    atm_iv_dec = float(np.interp(spot, all_strikes, all_ivs))
    atm_iv_pct = atm_iv_dec * 100.0

    # --- Plot ---
    fig, ax = plt.subplots(figsize=(10, 6))

    if len(put_strikes) > 0:
        ax.scatter(put_strikes, put_ivs * 100, label="Put IV", color="tomato",
                   marker="s", s=50, zorder=3)
    if len(call_strikes) > 0:
        ax.scatter(call_strikes, call_ivs * 100, label="Call IV", color="steelblue",
                   marker="o", s=50, zorder=3)

    # Horizontal dashed line at ATM IV — represents the BS flat-vol assumption
    ax.axhline(
        y=atm_iv_pct,
        color="red",
        linestyle="--",
        linewidth=1.8,
        label=f"BS flat vol assumption ({atm_iv_pct:.1f}%)",
    )

    ax.set_xlabel("Strike", fontsize=12)
    ax.set_ylabel("Implied Volatility (%)", fontsize=12)
    ax.set_title(f"Volatility Smile — {ticker_sym} {expiry}", fontsize=14)
    ax.legend(fontsize=10)
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig("volatility_smile.png", dpi=150, bbox_inches="tight")
    print("Saved volatility_smile.png")
    plt.show()


if __name__ == "__main__":
    main()
