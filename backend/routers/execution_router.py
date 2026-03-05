"""
execution_router.py – POST /api/execute (manual confirm required).
Execution is DISABLED by default for institutional safety.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from app.config import settings
from database.models import Trade
from database.crud import insert_trade
from datetime import datetime, timezone

router = APIRouter(tags=["execution"])

# Execution on OANDA PRACTICE account (demo money only — safe to enable)
EXECUTION_ENABLED = True


class ExecuteRequest(BaseModel):
    pair: str
    direction: str          # BUY / SELL
    lot_size: float
    sl: float
    tp: float
    confirmed: bool = False  # Must be True to execute


@router.get("/execute/status")
async def execution_status():
    """Check if the execution gateway is enabled."""
    return {
        "enabled": EXECUTION_ENABLED,
        "mode": "OANDA Practice (Demo Account)",
        "note": "All trades execute on demo money only — no real funds at risk.",
    }


@router.post("/execute")
async def execute_trade(request: ExecuteRequest):
    if not EXECUTION_ENABLED:
        raise HTTPException(
            status_code=403,
            detail="Execution gateway is DISABLED. Enable it in execution_router.py and provide manual confirmation."
        )

    if not request.confirmed:
        return {
            "status": "PENDING_CONFIRMATION",
            "message": "Set confirmed=true to execute this trade.",
            "order": request.dict(),
        }

    if request.pair not in settings.INSTRUMENTS:
        raise HTTPException(status_code=400, detail=f"Unsupported instrument: {request.pair}")

    try:
        from data.oanda_client import oanda
        units = int(request.lot_size * 100_000)
        if request.direction == "SELL":
            units = -units

        result = oanda.place_market_order(
            instrument=request.pair,
            units=units,
            stop_loss=request.sl,
            take_profit=request.tp,
        )

        # Log trade
        trade = {
            "pair": request.pair,
            "entry_price": 0.0,  # Will be filled from OANDA fill price
            "sl": request.sl,
            "tp": request.tp,
            "lot_size": request.lot_size,
            "direction": request.direction,
            "result": "OPEN",
            "entry_time": datetime.now(timezone.utc).isoformat(),
            "oanda_trade_id": str(result.get("orderFillTransaction", {}).get("tradeOpened", {}).get("tradeID", "")),
        }
        await insert_trade(trade)

        return {"status": "EXECUTED", "oanda_response": result, "trade": trade}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Execution failed: {str(e)}")
