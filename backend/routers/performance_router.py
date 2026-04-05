"""
performance_router.py – GET /api/performance
"""

from fastapi import APIRouter, Depends
from database.crud import get_metrics, get_recent_trades, get_recent_trades_by_user
from dependencies.auth import get_current_user
from features.performance_engine import PerformanceEngine

engine = PerformanceEngine()

router = APIRouter(tags=["performance"])


@router.get("/performance/{pair}")
async def get_performance(pair: str, current_email: str = Depends(get_current_user)):
    """Fetch analytics for a specific currency pair & current user."""
    # 1. Fetch user-specific trades for this pair
    trades = await get_recent_trades_by_user(current_email, limit=100)
    
    # 2. Filter for this pair
    pair_trades = [t for t in trades if t.get("pair") == pair]
    
    if not pair_trades:
        # Fallback to AI backtest mock if NO trades exist for this user & pair
        return engine.get_backtest_mock(pair)
    
    # 3. Compute metrics dynamically
    return engine.compute_metrics(pair_trades, pair=pair)


@router.get("/performance")
async def get_all_performance(current_email: str = Depends(get_current_user)):
    """Fetch global performance stats for the current user."""
    trades = await get_recent_trades_by_user(current_email, limit=300)
    if not trades:
        return {"ALL": engine.get_backtest_mock("ALL")}
    
    return {"ALL": engine.compute_metrics(trades, pair="ALL")}


@router.get("/trades/{pair}")
async def get_trades(pair: str, limit: int = 20):
    return await get_recent_trades(pair, limit=limit)
