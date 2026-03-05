"""
performance_router.py – GET /api/performance
"""

from fastapi import APIRouter
from database.crud import get_metrics, get_recent_trades

router = APIRouter(tags=["performance"])


@router.get("/performance/{pair}")
async def get_performance(pair: str):
    metrics = await get_metrics(pair)
    if not metrics:
        return {"pair": pair, "message": "No metrics available yet"}
    return metrics


@router.get("/performance")
async def get_all_performance():
    from app.config import settings
    results = {}
    for pair in settings.INSTRUMENTS:
        m = await get_metrics(pair)
        if m:
            results[pair] = m
    return results


@router.get("/trades/{pair}")
async def get_trades(pair: str, limit: int = 20):
    return await get_recent_trades(pair, limit=limit)
