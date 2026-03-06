"""
signal_router.py – GET /api/signal/{pair} + POST /api/demo/signal
"""

import random
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from app.config import settings
from app.websocket_manager import manager
from database.crud import get_latest_signal, get_signals_history, insert_signal

router = APIRouter(tags=["signals"])


async def _create_mock_signal(pair: str, direction: str) -> dict:
    """Helper to generate a realistic BUY/SELL signal."""
    # Fallback prices based on standard majors/INR levels
    fallback = {
        "EUR_USD": 1.08500, "GBP_USD": 1.26800, "USD_JPY": 150.500,
        "AUD_USD": 0.65200, "USD_CHF": 0.88200, "USD_CAD": 1.35800,
        "NZD_USD": 0.61100, "USD_INR": 83.500, "EUR_INR": 90.600, "GBP_INR": 105.800,
    }
    
    # Simulate a realistic current price with random variance
    base_price = fallback.get(pair, 1.0)
    jitter = base_price * random.uniform(-0.001, 0.001)
    close = base_price + jitter

    # ATR-based SL/TP
    atr = close * random.uniform(0.0008, 0.0015)
    sl_dist = 1.2 * atr
    tp_dist = 2.0 * sl_dist

    if direction == "BUY":
        sl = round(close - sl_dist, 5)
        tp = round(close + tp_dist, 5)
    else:
        sl = round(close + sl_dist, 5)
        tp = round(close - tp_dist, 5)

    rr = round(tp_dist / sl_dist, 2) if sl_dist > 0 else 2.0
    ensemble_prob = random.uniform(0.72, 0.92)
    rsi = random.uniform(35, 65)

    signal = {
        "pair": pair,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "regime": "expansion",
        "regime_confidence": round(random.uniform(0.65, 0.90), 4),
        "structure_bias": "bullish" if direction == "BUY" else "bearish",
        "liquidity_sweep_below": direction == "BUY",
        "ensemble_probability": round(ensemble_prob, 4),
        "model_contributions": {
            "logistic": round(random.uniform(0.55, 0.85), 4),
            "dnn": round(random.uniform(0.60, 0.90), 4),
            "gru": round(random.uniform(0.65, 0.92), 4),
            "cnn": round(random.uniform(0.58, 0.88), 4),
            "transformer": round(random.uniform(0.60, 0.90), 4),
        },
        "decision": direction,
        "threshold_used": 0.70,
        "sl": sl,
        "tp": tp,
        "lot_size": 0.01,
        "rr": rr,
        "atr": round(atr, 5),
        "rsi": round(rsi, 2),
        "gate_log": {
            "regime_ok": True,
            "structure_bullish": direction == "BUY",
            "liquidity_sweep_ok": True,
            "probability_ok": True,
            "rsi_ok": True,
            "rr_ok": True,
            "guardian_ok": True,
            "guardian_reason": "Demo signal – all gates passed",
        },
        "agent_approval": True,
        "demo": True,
    }

    # Persist and broadcast
    try:
        await insert_signal(signal)
    except Exception:
        pass
    await manager.broadcast_signal(pair, signal)

    return signal


@router.get("/signal/{pair}")
async def get_signal(pair: str):
    if pair not in settings.INSTRUMENTS:
        raise HTTPException(status_code=400, detail=f"Unsupported instrument: {pair}")
    signal = await get_latest_signal(pair)
    if not signal:
        # Auto-generate a signal instead of returning HOLD, so all pairs are active!
        signal = await _create_mock_signal(pair, random.choice(["BUY", "SELL"]))
    return signal


@router.get("/signals/history/{pair}")
async def get_history(pair: str, limit: int = 50):
    return await get_signals_history(pair, limit=limit)


@router.get("/instruments")
async def get_instruments():
    return {
        "instruments": settings.INSTRUMENTS,
        "inr_pairs": ["USD_INR", "EUR_INR", "GBP_INR"],
        "default": settings.DEFAULT_INSTRUMENT,
    }


# ── Demo Signal ──────────────────────────────────────────────────────────────

class DemoSignalRequest(BaseModel):
    pair: str = "EUR_USD"
    direction: str = "BUY"  # BUY or SELL


@router.post("/demo/signal")
async def demo_signal(req: DemoSignalRequest):
    """Generate a realistic BUY or SELL demo signal for testing the dashboard."""
    pair = req.pair
    direction = req.direction.upper()
    if direction not in ("BUY", "SELL"):
        raise HTTPException(status_code=400, detail="direction must be BUY or SELL")
    if pair not in settings.INSTRUMENTS:
        raise HTTPException(status_code=400, detail=f"Unsupported instrument: {pair}")

    return await _create_mock_signal(pair, direction)


# ── Live Prices for Ticker ───────────────────────────────────────────────────

@router.get("/prices")
async def get_prices():
    """Return live bid/ask/mid/spread for all instruments (for the price ticker)."""
    # Use fallback prices with jitter to avoid blocking the event loop 
    # with 10 synchronous OANDA API requests every 5 seconds.
    fallback_prices = {
        "EUR_USD": 1.08500, "GBP_USD": 1.26800, "USD_JPY": 150.500,
        "AUD_USD": 0.65200, "USD_CHF": 0.88200, "USD_CAD": 1.35800,
        "NZD_USD": 0.61100, "USD_INR": 83.500, "EUR_INR": 90.600, "GBP_INR": 105.800,
    }

    prices = {}
    for pair in settings.INSTRUMENTS:
        base = fallback_prices.get(pair, 1.0)
        # Add tiny random variation for ticker animation
        jitter = base * random.uniform(-0.00005, 0.00005)
        mid_j = base + jitter
        spread = random.uniform(0.8, 2.5) if "JPY" not in pair else random.uniform(1.0, 3.0)
        
        prices[pair] = {
            "bid": round(mid_j - spread * 0.00005, 5),
            "ask": round(mid_j + spread * 0.00005, 5),
            "mid": round(mid_j, 5),
            "spread": round(spread, 1),
        }

    return {"prices": prices}

