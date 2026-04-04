"""
account_router.py – Secure endpoints for personalized user data.
"""
from fastapi import APIRouter, Depends, HTTPException
from database.models import AccountSummaryResponse
from database import crud
from dependencies.auth import get_current_user
from typing import List

router = APIRouter(tags=["account"])

@router.get("/account/summary", response_model=AccountSummaryResponse)
async def get_account_summary(current_email: str = Depends(get_current_user)):
    user = await crud.get_user_by_email(current_email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    trades = await crud.get_recent_trades_by_user(user["email"])
    
    total_trades = len(trades)
    winning_trades = sum(1 for t in trades if t.get("result") == "win")
    win_rate = (winning_trades / total_trades) * 100 if total_trades > 0 else 0.0
    
    # Calculate total PnL from trades
    total_pnl = sum(float(t.get("pnl", 0.0)) for t in trades if "pnl" in t)
    
    return AccountSummaryResponse(
        balance=user["balance"],
        equity=user["balance"],  # Since all trades are simulated and closed instantly, balance = equity
        total_pnl=total_pnl,
        win_rate=win_rate,
        total_trades=total_trades
    )

@router.get("/account/trades")
async def get_account_trades(current_email: str = Depends(get_current_user), limit: int = 20):
    user = await crud.get_user_by_email(current_email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    trades = await crud.get_recent_trades_by_user(user["email"], limit=limit)
    return trades
