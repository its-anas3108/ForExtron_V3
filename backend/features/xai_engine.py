"""
xai_engine.py -- Explainable AI Signal Intelligence Engine
Generates human-readable, analyst-grade explanations for every trade signal.
Fully local, rule-based: no external API calls needed.
"""

import random
from typing import Dict, List, Any


def _compute_signal_grade(factors: List[dict]) -> str:
    """Compute a letter grade based on how many reasoning factors pass."""
    passed = sum(1 for f in factors if f["passed"])
    total = len(factors) if factors else 1
    ratio = passed / total
    if ratio >= 0.95:
        return "A+"
    elif ratio >= 0.85:
        return "A"
    elif ratio >= 0.75:
        return "B+"
    elif ratio >= 0.60:
        return "B"
    elif ratio >= 0.45:
        return "C"
    else:
        return "D"


GRADE_COLORS = {
    "A+": "#22c55e", "A": "#22c55e", "B+": "#3b82f6",
    "B": "#f59e0b", "C": "#f97316", "D": "#ef4444",
}


def _build_reasoning_factors(signal: dict) -> List[dict]:
    """Build a checklist of reasoning factors from the signal data."""
    factors = []
    gate_log = signal.get("gate_log", {})
    direction = signal.get("decision", "BUY")
    regime = signal.get("regime", "unknown")
    rsi = signal.get("rsi", 50)
    rr = signal.get("rr", 1.0)
    ensemble_prob = signal.get("ensemble_probability", 0.5)
    structure = signal.get("structure_bias", "neutral")
    sweep = signal.get("liquidity_sweep_below", False)
    model_contribs = signal.get("model_contributions", {})

    # 1. Market Regime
    regime_ok = gate_log.get("regime_ok", regime in ("expansion", "trending"))
    regime_label = regime.replace("_", " ").title() if regime else "Unknown"
    factors.append({
        "label": "Market Regime",
        "passed": regime_ok,
        "detail": f"{regime_label} regime detected -- favorable for directional trades" if regime_ok
        else f"{regime_label} regime detected -- caution advised for directional entries",
    })

    # 2. Structure Bias
    struct_ok = gate_log.get("structure_bullish", structure != "neutral") if direction == "BUY" \
        else gate_log.get("structure_bullish", True) is False
    bias_word = "Bullish" if direction == "BUY" else "Bearish"
    factors.append({
        "label": "Structure Bias",
        "passed": struct_ok,
        "detail": f"{bias_word} structure break confirmed on higher timeframe" if struct_ok
        else f"Structure does not strongly confirm {direction} bias",
    })

    # 3. Liquidity Sweep
    sweep_ok = gate_log.get("liquidity_sweep_ok", sweep)
    sweep_dir = "below" if direction == "BUY" else "above"
    sl_price = signal.get("sl", 0)
    factors.append({
        "label": "Liquidity Sweep",
        "passed": sweep_ok,
        "detail": f"Smart money liquidity sweep detected {sweep_dir} {sl_price:.5f}" if sweep_ok
        else f"No clear liquidity sweep detected {sweep_dir} key level",
    })

    # 4. Ensemble Probability
    prob_ok = gate_log.get("probability_ok", ensemble_prob >= 0.70)
    model_count = sum(1 for v in model_contribs.values() if v >= 0.5)
    total_models = max(len(model_contribs), 1)
    factors.append({
        "label": "Ensemble Agreement",
        "passed": prob_ok,
        "detail": f"{model_count}/{total_models} models agree on {direction} (probability: {ensemble_prob:.1%})",
    })

    # 5. RSI
    rsi_ok = gate_log.get("rsi_ok", 30 < rsi < 70)
    if direction == "BUY":
        rsi_comment = "not overbought" if rsi < 70 else "overbought -- caution"
    else:
        rsi_comment = "not oversold" if rsi > 30 else "oversold -- caution"
    factors.append({
        "label": "RSI Filter",
        "passed": rsi_ok,
        "detail": f"RSI at {rsi:.1f} -- {rsi_comment}, room for continuation" if rsi_ok
        else f"RSI at {rsi:.1f} -- {rsi_comment}",
    })

    # 6. Risk Reward
    rr_ok = gate_log.get("rr_ok", rr >= 1.5)
    factors.append({
        "label": "Risk-Reward Ratio",
        "passed": rr_ok,
        "detail": f"1:{rr:.1f} risk-reward -- {'above minimum threshold' if rr_ok else 'below recommended 1:1.5 minimum'}",
    })

    # 7. Risk Guardian
    guardian_ok = gate_log.get("guardian_ok", True)
    guardian_reason = gate_log.get("guardian_reason", "All risk checks passed")
    factors.append({
        "label": "Risk Guardian",
        "passed": guardian_ok,
        "detail": guardian_reason if isinstance(guardian_reason, str) else "Risk management checks completed",
    })

    return factors


def _compute_invalidation(signal: dict) -> dict:
    """Compute the price level where the trade thesis breaks."""
    direction = signal.get("decision", "BUY")
    sl = signal.get("sl", 0)
    entry = signal.get("entry", signal.get("close", 0))
    atr = signal.get("atr", abs(entry - sl) if entry and sl else 0.001)

    if direction == "BUY":
        invalidation_price = round(sl - atr * 0.3, 5)
        invalidation_text = f"If price closes below {invalidation_price:.5f}, bullish bias is invalidated. Consider exiting or reversing."
    else:
        invalidation_price = round(sl + atr * 0.3, 5)
        invalidation_text = f"If price closes above {invalidation_price:.5f}, bearish bias is invalidated. Consider exiting or reversing."

    return {
        "price": invalidation_price,
        "direction": direction,
        "description": invalidation_text,
    }


MARKET_CONTEXT_TEMPLATES = {
    "BUY": [
        "Momentum building after institutional liquidity grab. Dollar weakness supporting {pair_base} strength.",
        "Higher timeframe structure aligns with entry. Buyers stepping in at key demand zone.",
        "Risk-on sentiment favoring {pair_base}. Bond yield differential supports continuation.",
        "Breakout from consolidation zone with volume confirmation. Institutional flow aligned.",
        "Smart money accumulation detected. Price action confirms bullish displacement.",
    ],
    "SELL": [
        "Distribution pattern detected at supply zone. {pair_base} losing momentum against {pair_quote}.",
        "Risk-off flow supporting {pair_quote} strength. Lower highs forming on higher timeframe.",
        "Institutional selling pressure near resistance. Bearish displacement confirmed.",
        "Divergence between price and momentum indicators. Smart money exiting longs.",
        "Supply zone rejection with bearish engulfing pattern. Distribution phase active.",
    ],
}


def _generate_market_context(signal: dict) -> str:
    """Generate a one-line institutional-style market commentary."""
    direction = signal.get("decision", "BUY")
    pair = signal.get("pair", "EUR_USD")
    parts = pair.split("_")
    pair_base = parts[0] if len(parts) == 2 else pair[:3]
    pair_quote = parts[1] if len(parts) == 2 else pair[3:]

    templates = MARKET_CONTEXT_TEMPLATES.get(direction, MARKET_CONTEXT_TEMPLATES["BUY"])
    context = random.choice(templates)
    return context.format(pair_base=pair_base, pair_quote=pair_quote)


def _generate_recommendation(signal: dict, grade: str) -> dict:
    """Generate a risk assessment and recommendation."""
    ensemble_prob = signal.get("ensemble_probability", 0.5)
    rr = signal.get("rr", 1.0)
    direction = signal.get("decision", "BUY")

    if grade in ("A+", "A") and rr >= 2.0:
        risk_level = "LOW"
        risk_color = "#22c55e"
        text = f"High-conviction {direction} setup. Strong model consensus with favorable risk-reward. Consider standard position sizing."
    elif grade in ("B+", "B"):
        risk_level = "MEDIUM"
        risk_color = "#f59e0b"
        text = f"Moderate-conviction {direction} setup. Consider reduced position sizing or tighter stops. Monitor for confirmation."
    else:
        risk_level = "HIGH"
        risk_color = "#ef4444"
        text = f"Low-conviction setup. Multiple factors misaligned. Consider skipping or using minimal position size."

    return {
        "risk_level": risk_level,
        "risk_color": risk_color,
        "text": text,
    }


def _build_model_votes(signal: dict) -> List[dict]:
    """Build the per-model vote breakdown for visualization."""
    contribs = signal.get("model_contributions", {})
    direction = signal.get("decision", "BUY")
    threshold = signal.get("threshold_used", 0.70)

    model_display_names = {
        "logistic": "Logistic Regression",
        "dnn": "Deep Neural Network",
        "gru": "GRU (Sequential)",
        "cnn": "CNN (Pattern)",
        "transformer": "Transformer",
        "xgboost": "XGBoost",
    }

    votes = []
    for model_key, prob in contribs.items():
        agrees = prob >= 0.5
        votes.append({
            "model": model_display_names.get(model_key, model_key.upper()),
            "probability": round(prob, 4),
            "agrees": agrees,
            "vote": direction if agrees else ("SELL" if direction == "BUY" else "BUY"),
        })

    # Sort by probability descending
    votes.sort(key=lambda x: x["probability"], reverse=True)
    return votes


def generate_signal_intelligence(signal: dict) -> dict:
    """
    Master function: generates a complete XAI analysis for a trade signal.
    Returns everything needed for the Signal Intelligence panel.
    """
    if not signal or signal.get("decision") == "HOLD":
        return {
            "available": False,
            "message": "Signal Intelligence requires an active BUY or SELL signal.",
        }

    pair = signal.get("pair", "EUR_USD")
    direction = signal.get("decision", "BUY")
    ensemble_prob = signal.get("ensemble_probability", 0.5)

    # Build all components
    factors = _build_reasoning_factors(signal)
    grade = _compute_signal_grade(factors)
    invalidation = _compute_invalidation(signal)
    market_context = _generate_market_context(signal)
    recommendation = _generate_recommendation(signal, grade)
    model_votes = _build_model_votes(signal)

    passed_count = sum(1 for f in factors if f["passed"])
    total_count = len(factors)

    return {
        "available": True,
        "pair": pair,
        "direction": direction,
        "confidence": round(ensemble_prob, 4),
        "grade": grade,
        "grade_color": GRADE_COLORS.get(grade, "#94a3b8"),
        "factors": factors,
        "factors_passed": passed_count,
        "factors_total": total_count,
        "invalidation": invalidation,
        "market_context": market_context,
        "recommendation": recommendation,
        "model_votes": model_votes,
        "entry": signal.get("entry", signal.get("close", 0)),
        "sl": signal.get("sl", 0),
        "tp": signal.get("tp", 0),
        "rr": signal.get("rr", 0),
        "rsi": signal.get("rsi", 0),
        "regime": signal.get("regime", "unknown"),
    }
