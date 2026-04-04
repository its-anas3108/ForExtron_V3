"""
liquidity_router.py -- AI Liquidity & Pressure Map Endpoint
"""

from fastapi import APIRouter, HTTPException
import logging
from data.oanda_client import oanda
from features.liquidity_engine import generate_liquidity_map

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/liquidity/{instrument}")
async def get_liquidity(instrument: str):
    """
    Returns synthetic order book depth (Buy vs Sell pressure) for the given instrument.
    Requires live price to center the depth map.
    """
    try:
        # Get the current live price from the OANDA stream
        price_data = oanda.get_latest_price(instrument)
        if not price_data:
            # Fallback for testing if stream is disconnected
            logger.warning(f"No live price for {instrument}, using mock fallback.")
            current_price = 1.0500 if "JPY" not in instrument else 150.00
        else:
            current_price = price_data.get("mid", 1.0500)
            
        # Generate the synthetic order book
        liquidity_data = generate_liquidity_map(instrument, current_price)
        return liquidity_data

    except Exception as e:
        logger.error(f"Error generating liquidity map for {instrument}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to generate liquidity map")
