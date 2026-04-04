"""
execution_router.py – Simulated execution gateway mapping to individual users.
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, List
import random

from app.config import settings
from database.models import Trade
from database.crud import insert_trade, get_user_by_email, update_user_balance
from dependencies.auth import get_current_user
from datetime import datetime, timezone

router = APIRouter(tags=["execution"])

# Execution on simulated platform (safe to enable)
EXECUTION_ENABLED = True


class ExecuteRequest(BaseModel):
    pair: str
    direction: str          # BUY / SELL
    lot_size: float
    sl: float
    tp: float
    confirmed: bool = False
    num_trades: int = 1     # Multiplier for trades


@router.get("/execute/status")
async def execution_status():
    """Check if the execution gateway is enabled."""
    return {
        "enabled": EXECUTION_ENABLED,
        "mode": "Simulated Live Engine",
        "note": "All trades execute dynamically altering your virtual account balance.",
    }


@router.post("/execute")
async def execute_trade(request: ExecuteRequest, current_email: str = Depends(get_current_user)):
    if not EXECUTION_ENABLED:
        raise HTTPException(
            status_code=403,
            detail="Execution gateway is DISABLED."
        )

    if not request.confirmed:
        return {
            "status": "PENDING_CONFIRMATION",
            "message": "Set confirmed=true to execute this trade.",
            "order": request.dict(),
        }

    if request.pair not in settings.INSTRUMENTS:
        raise HTTPException(status_code=400, detail=f"Unsupported instrument: {request.pair}")

    user = await get_user_by_email(current_email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    # Cap maximum concurrent simulated trades to 50
    num_trades = min(max(1, request.num_trades), 50)

    try:
        # 1. Fetch live market price (pseudo-fetch/simulate here)
        from data.oanda_client import oanda
        try:
            live_price = float(oanda.get_prices(request.pair)[request.pair]["close"])
        except Exception:
            live_price = 1.0500  # Fallback
            
        total_pnl = 0.0
        trades_executed = []
            
        # 2. Simulate Result Loop
        for _ in range(num_trades):
            is_win = random.random() > 0.45 # 55% chance to win for sim purposes
            result_status = "win" if is_win else "loss"
            
            pip_diff = random.uniform(30, 80) if is_win else random.uniform(-60, -20)
            
            pnl = round(request.lot_size * pip_diff * 10, 2)
            total_pnl += pnl
            
            exit_price = round(live_price + (pip_diff * 0.0001 if request.direction == "BUY" else -pip_diff * 0.0001), 5)
            
            trade = {
                "user_email": current_email,
                "pair": request.pair,
                "entry_price": live_price,
                "exit_price": exit_price,
                "sl": request.sl,
                "tp": request.tp,
                "lot_size": request.lot_size,
                "direction": request.direction,
                "result": result_status,
                "pnl": pnl,
                "rr_achieved": round(abs(pnl) / (abs(pip_diff) * 10 * request.lot_size), 2),
                "entry_time": datetime.now(timezone.utc).isoformat(),
                "exit_time": datetime.now(timezone.utc).isoformat(),
                "oanda_trade_id": f"simulated-{random.randint(1000, 9999)}",
            }
            trades_executed.append(trade)
            
            # Log the Trade to MongoDB sequentially
            await insert_trade(trade)
            
        # 3. Alter User Balance Dynamically Once
        new_balance = user["balance"] + total_pnl
        await update_user_balance(current_email, new_balance)

        return {
            "status": "EXECUTED_AND_CLOSED",
            "message": f"{num_trades} trade(s) closed instantly for simulation. Total P&L: ${total_pnl:.2f}",
            "trades": trades_executed,
            "new_balance": new_balance,
            "total_pnl": total_pnl,
            "num_trades_executed": num_trades
        }

    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Execution failed: {str(e)}")
