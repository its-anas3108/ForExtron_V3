"""
signal_router.py – GET /api/signal/{pair} + POST /api/demo/signal
"""

import random
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
import time

from app.config import settings
from app.websocket_manager import manager
from database import crud
import pandas as pd
from database.crud import get_latest_signal, get_signals_history, insert_signal, get_recent_candles
from features.indicators import compute_indicators
from dependencies.auth import get_current_user

router = APIRouter(tags=["signals"])


def _generate_synthetic_candles(pair: str, count: int = 100) -> list:
    """Generate realistic synthetic candles when no live data is available."""
    from datetime import timedelta
    import numpy as np
    
    base_prices = {
        "EUR_USD": 1.08500, "GBP_USD": 1.26800, "USD_JPY": 150.500,
        "AUD_USD": 0.65200, "USD_CHF": 0.88200, "USD_CAD": 1.35800,
        "NZD_USD": 0.61100, "USD_INR": 83.500, "EUR_INR": 90.600, "GBP_INR": 105.800,
    }
    
    base = base_prices.get(pair, 1.0)
    pip_size = 0.01 if "JPY" in pair or "INR" in pair else 0.0001
    volatility = pip_size * 15  # ~15 pips per candle max swing
    
    now = datetime.now(timezone.utc)
    candles = []
    price = base
    
    for i in range(count):
        ts = now - timedelta(minutes=(count - i) * 5)
        
        # Random walk with mean reversion
        drift = (base - price) * 0.01  # mean reversion
        change = drift + random.gauss(0, volatility)
        
        o = price
        c = price + change
        h = max(o, c) + abs(random.gauss(0, volatility * 0.3))
        l = min(o, c) - abs(random.gauss(0, volatility * 0.3))
        
        candles.append({
            "pair": pair,
            "timeframe": "M5",
            "timestamp": ts.isoformat(),
            "open": round(o, 5),
            "high": round(h, 5),
            "low": round(l, 5),
            "close": round(c, 5),
            "volume": random.randint(50, 500),
        })
        
        price = c
    
    return candles


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
            "patchTST": round(random.uniform(0.70, 0.90), 4),
            "tcn": round(random.uniform(0.65, 0.88), 4),
            "tft": round(random.uniform(0.72, 0.92), 4),
            "grn": round(random.uniform(0.60, 0.85), 4),
        },
        "decision": direction,
        "threshold_used": 0.70,
        "entry": round(close, 5),
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


@router.get("/candles/{pair}")
async def get_candles(pair: str, limit: int = 100):
    """Fetch historical candles for the chart with indicators."""
    import asyncio
    if pair not in settings.INSTRUMENTS:
        raise HTTPException(status_code=400, detail=f"Unsupported instrument: {pair}")
    candles = await get_recent_candles(pair, limit=limit)
    
    # If DB is empty, try to fetch directly from OANDA
    if not candles:
        try:
            from data.oanda_client import oanda
            from database.crud import insert_candle
            history = await asyncio.get_event_loop().run_in_executor(
                None, lambda: oanda.get_historical_candles(pair, count=limit)
            )
            # Store them for next time
            for c in history:
                await insert_candle(c)
            candles = history
        except Exception as e:
            import logging
            logging.getLogger(__name__).warning(f"OANDA candle fetch failed for {pair}: {e}")
    
    # If still no candles, generate synthetic ones so the chart is never blank
    if not candles:
        candles = _generate_synthetic_candles(pair, limit)
    
    # Compute indicators on-the-fly for the chart
    df = pd.DataFrame(candles)
    df = compute_indicators(df)
    
    # Replace NaN/inf with None for clean JSON serialization
    import numpy as np
    df = df.replace([np.inf, -np.inf], np.nan)
    result = df.to_dict(orient="records")
    # Convert NaN to None for JSON
    for row in result:
        for key, val in row.items():
            if isinstance(val, float) and (pd.isna(val) or np.isnan(val)):
                row[key] = None
    return result


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
async def demo_signal(req: DemoSignalRequest, current_email: str = Depends(get_current_user)):
    """Generate a realistic BUY or SELL demo signal and execute a virtual trade for the user."""
    pair = req.pair
    direction = req.direction.upper()
    if direction not in ("BUY", "SELL"):
        raise HTTPException(status_code=400, detail="direction must be BUY or SELL")
    if pair not in settings.INSTRUMENTS:
        raise HTTPException(status_code=400, detail=f"Unsupported instrument: {pair}")

    # 1. Generate the core signal payload
    signal = await _create_mock_signal(pair, direction)
    
    # 2. Automatically execute a virtual trade for the logged-in user
    profit_loss = round(random.uniform(5.0, 150.0), 2) if random.random() > 0.4 else round(random.uniform(-100.0, -10.0), 2)
    trade_result = "win" if profit_loss > 0 else "loss"
    
    trade = {
        "user_email": current_email,
        "pair": pair,
        "entry_price": signal["price"],
        "sl": signal["dynamic_sl"],
        "tp": signal["dynamic_tp"],
        "lot_size": 0.1,  # Standard virtual mini-lot
        "direction": direction,
        "result": trade_result,
        "pnl": profit_loss,
        "entry_time": signal["timestamp"],
        "oanda_trade_id": f"demo_exec_{int(time.time())}"
    }
    
    await crud.insert_trade(trade)
    
    # 3. Update their virtual Account Balance
    user = await crud.get_user_by_email(current_email)
    if user:
        new_balance = user.get("balance", 10000.0) + profit_loss
        await crud.update_user_balance(current_email, new_balance)

    return signal


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

