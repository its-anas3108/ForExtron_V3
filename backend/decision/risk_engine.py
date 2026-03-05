"""
risk_engine.py – Position sizing and SL/TP calculation.

Formula:
  SL   = 1.2 × ATR
  TP   = 2.0 × SL
  Lot  = (Balance × RISK_PCT) / (SL × pip_value)
"""

import logging
import pandas as pd
from app.config import settings

logger = logging.getLogger(__name__)

# Pip values per instrument (approximate in USD base)
PIP_VALUE_MAP = {
    "EUR_USD": 10.0,
    "GBP_USD": 10.0,
    "USD_JPY": 9.09,
    "AUD_USD": 10.0,
    "USD_CHF": 10.0,
    "USD_CAD": 7.69,
    "NZD_USD": 10.0,
    "USD_INR": 12.5,   # 1 pip ≈ ₹0.0001 × 100,000 units × conversion
    "EUR_INR": 12.5,
    "GBP_INR": 12.5,
}


class RiskEngine:

    def calculate(
        self,
        df: pd.DataFrame,
        balance: float = 10000.0,
        instrument: str = "EUR_USD",
    ) -> dict:
        try:
            atr = float(df["atr"].iloc[-1])
            close = float(df["close"].iloc[-1])
        except (KeyError, IndexError):
            return {"sl": None, "tp": None, "lot_size": None, "rr": 0.0}

        if atr <= 0:
            return {"sl": None, "tp": None, "lot_size": None, "rr": 0.0}

        # ── SL and TP ──────────────────────────────────────────────────────
        sl_distance = settings.ATR_SL_MULTIPLIER * atr
        tp_distance = settings.RR_MINIMUM * sl_distance

        sl_price = round(close - sl_distance, 5)   # For BUY
        tp_price = round(close + tp_distance, 5)

        # ── R:R ───────────────────────────────────────────────────────────
        rr = tp_distance / sl_distance if sl_distance > 0 else 0.0

        # ── Position Size (lots) ──────────────────────────────────────────
        pip_value = PIP_VALUE_MAP.get(instrument, 10.0)
        risk_amount = balance * settings.RISK_PER_TRADE_PCT
        sl_pips = (sl_distance / 0.0001) if "JPY" not in instrument else (sl_distance / 0.01)
        lot_size = round(risk_amount / (sl_pips * pip_value), 2) if sl_pips > 0 else 0.01

        return {
            "sl": sl_price,
            "tp": tp_price,
            "sl_distance_pips": round(sl_pips, 1),
            "tp_distance_pips": round(sl_pips * settings.RR_MINIMUM, 1),
            "lot_size": max(0.01, min(lot_size, 10.0)),
            "rr": round(rr, 2),
            "risk_amount_usd": round(risk_amount, 2),
        }
