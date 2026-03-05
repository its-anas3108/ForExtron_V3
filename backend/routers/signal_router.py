"""
signal_router.py – GET /api/signal/{pair}
"""

from fastapi import APIRouter, HTTPException
from app.config import settings
from database.crud import get_latest_signal, get_signals_history

router = APIRouter(tags=["signals"])


@router.get("/signal/{pair}")
async def get_signal(pair: str):
    if pair not in settings.INSTRUMENTS:
        raise HTTPException(status_code=400, detail=f"Unsupported instrument: {pair}")
    signal = await get_latest_signal(pair)
    if not signal:
        return {"pair": pair, "decision": "HOLD", "message": "No signal available yet"}
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
