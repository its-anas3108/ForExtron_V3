"""
currency_router.py -- GET /api/currency/strength
Returns the global forex AI currency intelligence map.
"""

from fastapi import APIRouter
from routers.signal_router import get_prices
from features.currency_engine import calculate_currency_strength

router = APIRouter(tags=["currency"])


@router.get("/currency/strength")
async def get_currency_strength():
    """
    Fetches live prices for all tracked pairs and computes the relative strength
    score (0-100%) for each individual baseline fiat currency (USD, EUR, GBP, etc.).
    Returns dynamic AI insights based on the strongest/weakest divergence.
    """
    
    # 1. Fetch current live prices from the OANDA router/mock generator
    # get_prices returns {"prices": {"EUR_USD": {"bid": 1.0, "ask": 1.0, "mid": 1.05...}, ...}}
    price_data = await get_prices()
    all_prices = price_data.get("prices", {})

    # 2. Run the currency intelligence engine
    result = calculate_currency_strength(all_prices)

    return result
