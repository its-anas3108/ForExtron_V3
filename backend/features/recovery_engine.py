"""
recovery_engine.py -- AI Opportunity Recovery Engine
Analyzes previously completed or missed signals against the current market
price to determine if they are still viable ("recoverable").
"""

from datetime import datetime, timezone
import math


def analyze_opportunity(signal: dict, current_price: dict) -> dict:
    """
    Evaluates a past signal against the current price.
    current_price expects a dict like: {"bid": 1.085, "ask": 1.0852, "mid": 1.0851, "spread": 2.0}
    Returns a dict with recovery status, reasoning, and visual data.
    """
    pair = signal.get("pair", "EUR_USD")
    direction = signal.get("decision", "BUY")
    timestamp_str = signal.get("timestamp", datetime.now(timezone.utc).isoformat())
    
    # Calculate time ago
    try:
        sig_time = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
        now = datetime.now(timezone.utc)
        diff = now - sig_time
        minutes_ago = int(diff.total_seconds() / 60)
    except Exception:
        minutes_ago = 60

    if minutes_ago < 1:
        time_text = "Just now"
    elif minutes_ago < 60:
        time_text = f"{minutes_ago} minutes ago"
    else:
        hours = minutes_ago // 60
        mins = minutes_ago % 60
        time_text = f"{hours}h {mins}m ago"

    mid = current_price.get("mid", 0)
    bid = current_price.get("bid", mid)
    ask = current_price.get("ask", mid)
    
    # Execution price depends on direction
    exec_price = ask if direction == "BUY" else bid
    
    entry = signal.get("entry", signal.get("close", 0))
    sl = signal.get("sl", 0)
    tp = signal.get("tp", 0)
    conf = signal.get("ensemble_probability", 0.5)

    if not entry or not sl or not tp:
        return {
            "valid": False,
            "status": "EXPIRED",
            "message": f"Signal missing key price data. Entry: {entry}, SL: {sl}, TP: {tp}",
            "color": "#94a3b8"
        }

    # Calculate distance moved as percentage of TP distance
    total_tp_dist = abs(tp - entry)
    total_sl_dist = abs(sl - entry)
    
    if total_tp_dist == 0: total_tp_dist = 0.001
    if total_sl_dist == 0: total_sl_dist = 0.001

    if direction == "BUY":
        moved_towards_tp = exec_price - entry
        is_tp_hit = exec_price >= tp
        is_sl_hit = exec_price <= sl
    else:
        moved_towards_tp = entry - exec_price
        is_tp_hit = exec_price <= tp
        is_sl_hit = exec_price >= sl

    # 1. Check if already hit TP
    if is_tp_hit:
        return {
            "pair": pair,
            "direction": direction,
            "time_text": time_text,
            "confidence": conf,
            "status": "EXPIRED",
            "status_text": "Opportunity Expired",
            "color": "#ef4444", # Red
            "assessment": f"Price has already reached the take profit level of {tp:.5f}. The move is complete.",
            "recommendation": "Do not enter. Wait for new setup."
        }

    # 2. Check if already hit SL (Invalidated)
    if is_sl_hit:
        return {
            "pair": pair,
            "direction": direction,
            "time_text": time_text,
            "confidence": conf,
            "status": "INVALIDATED",
            "status_text": "Setup Invalidated",
            "color": "#ef4444", # Red
            "assessment": f"Market structure broke and price hit the invalidation level of {sl:.5f}.",
            "recommendation": "Setup is void. Do not enter."
        }

    # 3. Check distance moved
    pct_to_tp = (moved_towards_tp / total_tp_dist) * 100
    pips_moved = abs(exec_price - entry) * (10000 if "JPY" not in pair else 100)
    
    if pct_to_tp > 40:
        # Moved too far, risky to chase
        return {
            "pair": pair,
            "direction": direction,
            "time_text": time_text,
            "confidence": conf,
            "status": "RISKY",
            "status_text": "Late Entry / Risky",
            "color": "#f59e0b", # Yellow
            "assessment": f"Price has already moved {pct_to_tp:.1f}% towards the take profit." +
                          (f" Market regime may be shifting." if minutes_ago > 120 else " Risk-reward is now compromised."),
            "recommendation": "Entering now severely reduces R:R. Consider a pullback limit order or skip."
        }
    
    elif pct_to_tp < -20:
        # In drawdown but SL not hit yet
        return {
            "pair": pair,
            "direction": direction,
            "time_text": time_text,
            "confidence": conf,
            "status": "RISKY",
            "status_text": "In Drawdown",
            "color": "#f59e0b", # Yellow
            "assessment": f"Price is currently trading {abs(pct_to_tp):.1f}% against the original entry in drawdown territory.",
            "recommendation": f"Market structure is still {signal.get('structure_bias', 'intact')}, but momentum is opposing. High risk."
        }

    else:
        # Still very close to entry (between -20% drawdown and +40% profit)
        move_pct_total = (abs(exec_price - entry) / entry) * 100
        return {
            "pair": pair,
            "direction": direction,
            "time_text": time_text,
            "confidence": conf,
            "status": "VALID",
            "status_text": "Still Valid",
            "color": "#22c55e", # Green
            "assessment": f"Price has only moved {move_pct_total:.3f}% from the original entry zone. " +
                          f"Market structure remains {signal.get('structure_bias', 'favorable')} and liquidity imbalance is still present.",
            "recommendation": f"This opportunity is still actionable. Suggested entry zone: {entry:.5f} \u00b1 {total_sl_dist*0.1:.5f}"
        }
