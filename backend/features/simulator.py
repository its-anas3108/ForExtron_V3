"""
simulator.py – Monte Carlo Trade Outcome Predictor
Uses Geometric Brownian Motion to simulate future price paths
and compute TP/SL hit probabilities.
"""

import math
import random
from typing import Dict, List, Any


def monte_carlo_simulate(
    price: float,
    volatility: float,
    direction: str,
    sl: float,
    tp: float,
    n_sims: int = 500,
    horizon_steps: int = 120,
    dt: float = 1 / 1440,  # 1 minute in trading-day fraction
) -> Dict[str, Any]:
    """
    Run Monte Carlo simulation using Geometric Brownian Motion.

    Args:
        price:        Current mid price
        volatility:   Annualized volatility (e.g. 0.08 for 8%)
        direction:    'BUY' or 'SELL'
        sl:           Stop-loss price level
        tp:           Take-profit price level
        n_sims:       Number of simulation paths
        horizon_steps: Number of time steps (minutes)
        dt:           Time step size as fraction of year

    Returns:
        Dictionary with probabilities, sampled paths, and cone bounds.
    """
    is_buy = direction.upper() == "BUY"

    # Small positive drift toward the signal direction
    drift = 0.02 if is_buy else -0.02

    tp_hits = 0
    sl_hits = 0
    breakeven = 0

    all_final_prices = []
    sampled_paths = []
    all_paths_for_cone = []

    sample_indices = set(random.sample(range(n_sims), min(12, n_sims)))

    for i in range(n_sims):
        path = [price]
        current = price
        hit_tp = False
        hit_sl = False

        for step in range(horizon_steps):
            # Geometric Brownian Motion step
            z = random.gauss(0, 1)
            change = current * (drift * dt + volatility * math.sqrt(dt) * z)
            current = current + change
            current = max(current, price * 0.90)  # Floor at -10%
            path.append(round(current, 5))

            # Check if TP or SL hit
            if is_buy:
                if current >= tp:
                    hit_tp = True
                    break
                if current <= sl:
                    hit_sl = True
                    break
            else:
                if current <= tp:
                    hit_tp = True
                    break
                if current >= sl:
                    hit_sl = True
                    break

        # Pad path to full horizon if it terminated early
        while len(path) < horizon_steps + 1:
            path.append(path[-1])

        if hit_tp:
            tp_hits += 1
        elif hit_sl:
            sl_hits += 1
        else:
            breakeven += 1

        all_final_prices.append(path[-1])
        all_paths_for_cone.append(path)

        if i in sample_indices:
            # Downsample path to 30 points for frontend rendering
            step_size = max(1, len(path) // 30)
            sampled_paths.append(path[::step_size])

    # Compute probability cone (percentile bands at each time step)
    cone_upper = []
    cone_lower = []
    median_path = []
    cone_p10 = []
    cone_p90 = []

    for step in range(horizon_steps + 1):
        prices_at_step = sorted([p[step] for p in all_paths_for_cone])
        n = len(prices_at_step)
        cone_lower.append(round(prices_at_step[int(n * 0.05)], 5))
        cone_p10.append(round(prices_at_step[int(n * 0.10)], 5))
        median_path.append(round(prices_at_step[n // 2], 5))
        cone_p90.append(round(prices_at_step[int(n * 0.90)], 5))
        cone_upper.append(round(prices_at_step[int(n * 0.95)], 5))

    # Best and worst paths (by final price)
    final_prices_indexed = [(all_paths_for_cone[i][-1], i) for i in range(n_sims)]
    final_prices_indexed.sort()
    worst_idx = final_prices_indexed[0][1]
    best_idx = final_prices_indexed[-1][1]

    step_size = max(1, (horizon_steps + 1) // 30)
    best_path = all_paths_for_cone[best_idx][::step_size]
    worst_path = all_paths_for_cone[worst_idx][::step_size]
    median_downsampled = median_path[::step_size]

    return {
        "entry_price": price,
        "direction": direction.upper(),
        "sl": sl,
        "tp": tp,
        "horizon_minutes": horizon_steps,
        "num_simulations": n_sims,
        "tp_probability": round(tp_hits / n_sims * 100, 1),
        "sl_probability": round(sl_hits / n_sims * 100, 1),
        "breakeven_probability": round(breakeven / n_sims * 100, 1),
        "median_final_price": round(sorted(all_final_prices)[n_sims // 2], 5),
        "median_path": median_downsampled,
        "best_path": best_path,
        "worst_path": worst_path,
        "cone_upper": cone_upper[::step_size],
        "cone_lower": cone_lower[::step_size],
        "cone_p90": cone_p90[::step_size],
        "cone_p10": cone_p10[::step_size],
        "sampled_paths": sampled_paths,
    }
