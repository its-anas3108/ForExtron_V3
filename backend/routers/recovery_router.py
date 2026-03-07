"""
recovery_router.py -- GET /api/recovery/{pair}
Returns a list of missed opportunities analyzed against current price.
"""

from fastapi import APIRouter
from typing import List
from database.crud import get_signals_history
from routers.signal_router import get_prices
from features.recovery_engine import analyze_opportunity

router = APIRouter(tags=["recovery"])


@router.get("/recovery/{pair}")
async def get_recovery_opportunities(pair: str):
    """
    Fetches the 5 most recent actionable signals for the pair, checks live prices,
    and returns an AI Market Intelligence Report of what the user missed.
    """
    # Get last 10 signals to find at least a few directional ones
    history = await get_signals_history(pair, limit=10)
    
    # Filter out HOLDs and very old ones (optional filtering)
    actionable = [s for s in history if s.get("decision") in ("BUY", "SELL")]
    
    # Take top 4 most recent
    missed_signals = actionable[:4]
    
    if not missed_signals:
        return {"opportunities": []}

    # Fetch current live prices
    # get_prices returns {"prices": {"EUR_USD": {"bid": 1.0, ...}}}
    price_data = await get_prices()
    all_prices = price_data.get("prices", {})
    current_price = all_prices.get(pair, {"bid": 1.0, "ask": 1.0, "mid": 1.0, "spread": 0.0})

    # Analyze each missed signal
    opportunities = []
    for sig in missed_signals:
        analysis = analyze_opportunity(sig, current_price)
        opportunities.append(analysis)

    return {"opportunities": opportunities}
