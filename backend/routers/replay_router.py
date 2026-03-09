"""
replay_router.py – POST /api/replay/analyze
Analyzes a completed trade and returns explanatory factors + AI insights.
"""

from fastapi import APIRouter
from pydantic import BaseModel, Field
from typing import Dict, Optional, Any
from features.replay_engine import analyze_trade

router = APIRouter(tags=["replay"])


class TradeReplayRequest(BaseModel):
    model_config = {"protected_namespaces": ()}

    pair: str = "EUR_USD"
    direction: str = "BUY"
    entry: float = 1.0850
    sl: float = 1.0820
    tp: float = 1.0910
    result: Optional[str] = "loss"
    pnl: Optional[float] = -15.0
    regime: Optional[str] = "expansion"
    confidence: Optional[float] = 0.72
    gate_log: Optional[Dict[str, Any]] = None
    model_contributions: Optional[Dict[str, float]] = None
    duration_minutes: Optional[int] = 45


@router.post("/replay/analyze")
async def replay_analyze(req: TradeReplayRequest):
    trade_data = req.model_dump()
    # Provide sensible defaults if not supplied
    if not trade_data.get("gate_log"):
        trade_data["gate_log"] = {
            "regime_ok": True,
            "structure_bullish": True,
            "liquidity_sweep_ok": True,
            "probability_ok": True,
            "rsi_ok": True,
            "rr_ok": True,
            "guardian_ok": True,
        }
    if not trade_data.get("model_contributions"):
        trade_data["model_contributions"] = {
            "logistic": 0.55,
            "dnn": 0.68,
            "gru": 0.72,
            "cnn": 0.61,
            "transformer": 0.58,
        }
    return analyze_trade(trade_data)
