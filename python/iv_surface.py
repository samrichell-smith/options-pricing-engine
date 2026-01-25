"""
Plots the implied volatility surface as a 2D heatmap across strike and expiry.

Fetches live option chain data from Yahoo Finance, computes IV per strike/expiry
via Newton-Raphson, and plots a pcolormesh where colour encodes IV (%).

Usage:
    python3 iv_surface.py [--ticker TICKER]
"""

import argparse
import sys
import os
from datetime import datetime, timedelta

import matplotlib.pyplot as plt
import numpy as np
import yfinance as yf

sys.path.insert(0, os.path.dirname(__file__))
import options_pricer as op
from implied_vol import implied_vol

# Liquidity / filtering constants (same as volatility_smile.py)
MAX_SPREAD_RATIO = 0.50
STRIKE_BAND      = 0.20
RISK_FREE_RATE   = 0.05

# Target expiries in days; accept if within ±20 days of target
TARGET_DAYS  = [30, 60, 90, 180]
MAX_DAY_DIFF = 20
MIN_EXPIRIES = 2


def select_expiries(ticker_obj) -> list[tuple[str, int]]:
    """
    Return up to 4 expiry strings closest to TARGET_DAYS, one per target.

    Each entry is (expiry_str, days_to_expiry). Skips targets where the
    nearest available expiry is further than MAX_DAY_DIFF days away.
    """
    today    = datetime.today().date()
    all_exp  = ticker_obj.options          # tuple of "YYYY-MM-DD" strings
    selected = {}                          # target_days -> (expiry_str, days)

    for target in TARGET_DAYS:
        target_date = today + timedelta(days=target)
        best = min(
            all_exp,
            key=lambda e: abs((datetime.strptime(e, "%Y-%m-%d").date() - target_date).days),
        )
        best_date = datetime.strptime(best, "%Y-%m-%d").date()
        diff = abs((best_date - target_date).days)
        if diff <= MAX_DAY_DIFF:
            days = (best_date - today).days
            selected[target] = (best, days)

    # Deduplicate: same expiry may match multiple targets; keep by target order
    seen, result = set(), []
    for target in TARGET_DAYS:
        if target in selected:
            exp_str, days = selected[target]
            if exp_str not in seen:
                seen.add(exp_str)
                result.append((exp_str, days))

    return result


def compute_ivs_for_expiry(
    chain_df, spot: float, T: float, option_type: op.OptionType
) -> dict[float, float]:
    """
    Compute IV (decimal) per strike for one expiry/option-type combination.

    Applies liquidity filters and ±STRIKE_BAND strike window.
    Returns {strike: iv_decimal}.
    """
    low  = spot * (1.0 - STRIKE_BAND)
    high = spot * (1.0 + STRIKE_BAND)
    ivs  = {}

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
            ivs[strike] = iv
        except ValueError:
            continue

    return ivs


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Plot the implied volatility surface across strikes and expiries."
    )
    parser.add_argument("--ticker", default="SPY",
                        help="Underlying ticker (default: SPY)")
    args = parser.parse_args()
    ticker_sym = args.ticker.upper()

    print(f"Fetching data for {ticker_sym}...")
    stock = yf.Ticker(ticker_sym)

    spot = float(stock.fast_info["lastPrice"])
    print(f"Spot: {spot:.2f}")

    expiries = select_expiries(stock)
    if len(expiries) < MIN_EXPIRIES:
        print(
            f"Warning: only {len(expiries)} expiry/ies available near target dates "
            f"(need at least {MIN_EXPIRIES}). "
            "This is expected outside US market hours or for illiquid tickers."
        )
        sys.exit(1)

    print(f"Selected {len(expiries)} expiries: "
          + ", ".join(f"{e} ({d}d)" for e, d in expiries))

    today = datetime.today().date()

    # Collect IV dicts per expiry: {expiry_str: {strike: iv}}
    expiry_iv_maps: list[tuple[int, dict[float, float]]] = []

    for exp_str, days in expiries:
        T = (datetime.strptime(exp_str, "%Y-%m-%d").date() - today).days / 365.0
        if T <= 0:
            continue

        chain = stock.option_chain(exp_str)

        # Use calls for OTM calls (strike > spot) and puts for OTM puts (strike < spot)
        call_ivs = compute_ivs_for_expiry(chain.calls, spot, T, op.OptionType.CALL)
        put_ivs  = compute_ivs_for_expiry(chain.puts,  spot, T, op.OptionType.PUT)

        # Merge: prefer put IV below spot, call IV above (standard surface convention)
        merged: dict[float, float] = {}
        for k, v in put_ivs.items():
            if k <= spot:
                merged[k] = v
        for k, v in call_ivs.items():
            if k > spot:
                merged[k] = v
        # Fill any gaps with whichever side has data
        for k, v in call_ivs.items():
            if k not in merged:
                merged[k] = v
        for k, v in put_ivs.items():
            if k not in merged:
                merged[k] = v

        if merged:
            expiry_iv_maps.append((days, merged))
            print(f"  {exp_str} ({days}d): {len(merged)} liquid strikes")
        else:
            print(f"  {exp_str} ({days}d): no liquid data — skipped")

    if len(expiry_iv_maps) < MIN_EXPIRIES:
        print(
            f"Warning: only {len(expiry_iv_maps)} expiry/ies have liquid data "
            f"(need at least {MIN_EXPIRIES}). "
            "Check market hours or choose a more liquid ticker."
        )
        sys.exit(1)

    # Inner join: strikes present in ALL expiries
    strike_sets = [set(iv_map.keys()) for _, iv_map in expiry_iv_maps]
    common_strikes = sorted(strike_sets[0].intersection(*strike_sets[1:]))

    if len(common_strikes) < 3:
        print(
            f"Warning: only {len(common_strikes)} common strike(s) across all expiries. "
            "Try a more liquid ticker or re-run during market hours."
        )
        sys.exit(1)

    # Sort expiry rows ascending by days-to-expiry
    expiry_iv_maps.sort(key=lambda x: x[0])
    expiry_days_list = [days for days, _ in expiry_iv_maps]

    print(f"\nBuilding {len(expiry_days_list)}×{len(common_strikes)} IV grid...")

    # Build 2D grid: rows = expiries, cols = strikes, values = IV %
    iv_grid = np.full((len(expiry_days_list), len(common_strikes)), np.nan)
    for i, (_, iv_map) in enumerate(expiry_iv_maps):
        for j, strike in enumerate(common_strikes):
            if strike in iv_map:
                iv_grid[i, j] = iv_map[strike] * 100.0  # decimal -> %

    strikes_arr = np.array(common_strikes)
    days_arr    = np.array(expiry_days_list)

    # --- Plot ---
    fig, ax = plt.subplots(figsize=(12, 5))

    mesh = ax.pcolormesh(
        strikes_arr, days_arr, iv_grid,
        cmap="RdYlGn_r",
        shading="auto",
    )

    cbar = plt.colorbar(mesh, ax=ax)
    cbar.set_label("Implied Volatility (%)", fontsize=11)

    # ATM vertical line
    ax.axvline(spot, color="white", linestyle="--", linewidth=1.5,
               label=f"ATM ({spot:.0f})")

    ax.set_xlabel("Strike", fontsize=12)
    ax.set_ylabel("Days to Expiry", fontsize=12)
    ax.set_title(f"Implied Volatility Surface — {ticker_sym}", fontsize=14)

    # Label each row with its day count
    ax.set_yticks(days_arr)
    ax.set_yticklabels([str(d) for d in days_arr])

    ax.legend(fontsize=10, loc="upper left")
    plt.tight_layout()
    plt.savefig("iv_surface.png", dpi=150, bbox_inches="tight")
    print("Saved iv_surface.png")
    plt.show()


if __name__ == "__main__":
    main()
