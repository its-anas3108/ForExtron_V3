"""
xai_router.py -- POST /api/xai/analyze
Explainable AI Signal Intelligence endpoints.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Optional
from features.xai_engine import generate_signal_intelligence

router = APIRouter(tags=["xai"])


class XAIRequest(BaseModel):
    model_config = {"protected_namespaces": ()}

    pair: str = "EUR_USD"
    decision: str = "BUY"
    regime: Optional[str] = "expansion"
    regime_confidence: Optional[float] = 0.75
    structure_bias: Optional[str] = "bullish"
    liquidity_sweep_below: Optional[bool] = True
    ensemble_probability: Optional[float] = 0.72
    model_contributions: Optional[Dict[str, float]] = None
    threshold_used: Optional[float] = 0.70
    sl: Optional[float] = 0
    tp: Optional[float] = 0
    entry: Optional[float] = 0
    rr: Optional[float] = 2.0
    atr: Optional[float] = 0.001
    rsi: Optional[float] = 50.0
    gate_log: Optional[Dict] = None
    lot_size: Optional[float] = 0.01


@router.post("/xai/analyze")
async def xai_analyze(req: XAIRequest):
    """Generate a full XAI Signal Intelligence analysis for the given signal."""
    signal_data = req.model_dump()
    result = generate_signal_intelligence(signal_data)
    return result
