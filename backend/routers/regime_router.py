"""
regime_router.py – GET /api/regime/{pair}
"""

from fastapi import APIRouter
from database.crud import get_latest_signal
from features.regime_features import REGIME_COLORS

router = APIRouter(tags=["regime"])


@router.get("/regime/{pair}")
async def get_regime(pair: str):
    signal = await get_latest_signal(pair)
    if not signal:
        return {"pair": pair, "regime": "unknown", "color": "#6B7280"}
    regime = signal.get("regime", "unknown")
    return {
        "pair": pair,
        "regime": regime,
        "regime_confidence": signal.get("regime_confidence"),
        "color": REGIME_COLORS.get(regime, "#6B7280"),
        "structure_bias": signal.get("structure_bias"),
        "timestamp": signal.get("timestamp"),
    }
