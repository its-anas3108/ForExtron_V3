"""
liquidity_engine.py -- AI Liquidity & Pressure Map

Calculates synthetic order book depth (Buy vs Sell pressure) based on live price action.
Generates 10 liquidity levels (5 resistance, 5 support) and an AI insight alert.
"""

import math
from typing import Dict, List, Any

# Standard tick sizes for estimation
TICK_SIZES = {
    "EUR_USD": 0.0001,
    "GBP_USD": 0.0001,
    "AUD_USD": 0.0001,
    "NZD_USD": 0.0001,
    "USD_CAD": 0.0001,
    "USD_CHF": 0.0001,
    "USD_JPY": 0.01,
    "EUR_JPY": 0.01,
    "GBP_JPY": 0.01,
    "EUR_GBP": 0.0001,
}

def generate_liquidity_map(instrument: str, current_price: float) -> Dict[str, Any]:
    """
    Generates a synthetic market depth map around the given current price.
    Returns the levels, pressure percentages, and an AI insight alert.
    """
    tick_size = TICK_SIZES.get(instrument, 0.0001)
    
    # We want levels at 10-tick intervals
    level_spacing = tick_size * 10
    
    # Round current price to nearest 10-tick interval for cleaner levels
    base_level = round(current_price / level_spacing) * level_spacing
    
    levels = []
    
    # Generate 5 levels above (Resistance / Sell Walls)
    for i in range(5, 0, -1):
        price = base_level + (i * level_spacing)
        
        # Synthetic pressure logic based on distance and price ending
        # The further away, generally the more resting liquidity builds up
        sell_pressure = 40 + (i * 10) # 50% to 90%
        
        # Determine if it's a "psychological" round number (ends in 00 or 50)
        # We check the 4th decimal for non-JPY pairs, 2nd for JPY
        decimals = 2 if instrument.endswith("JPY") else 4
        price_str = f"{price:.{decimals}f}"
        if price_str.endswith("00") or price_str.endswith("50"):
            sell_pressure += 15 # Add extra weight to round numbers
            
        # Ensure bounds
        sell_pressure = min(98, max(2, sell_pressure))
        buy_pressure = 100 - sell_pressure
        
        levels.append({
            "price": price_str,
            "type": "resistance",
            "buy_pressure": int(buy_pressure),
            "sell_pressure": int(sell_pressure),
            "total_volume": int(sell_pressure * 1.5) # Arbitrary visual scale
        })
        
    # Generate 5 levels below (Support / Buy Walls)
    for i in range(1, 6):
        price = base_level - (i * level_spacing)
        
        # Synthetic pressure logic based on distance
        buy_pressure = 40 + (i * 10) # 50% to 90%
        
        decimals = 2 if instrument.endswith("JPY") else 4
        price_str = f"{price:.{decimals}f}"
        if price_str.endswith("00") or price_str.endswith("50"):
            buy_pressure += 15
            
        # Ensure bounds
        buy_pressure = min(98, max(2, buy_pressure))
        sell_pressure = 100 - buy_pressure
        
        levels.append({
            "price": price_str,
            "type": "support",
            "buy_pressure": int(buy_pressure),
            "sell_pressure": int(sell_pressure),
            "total_volume": int(buy_pressure * 1.5)
        })
        
    # Analyze the book to generate an AI Alert
    # Find the strongest buy and sell walls
    strongest_sell = max([l for l in levels if l["type"] == "resistance"], key=lambda x: x["sell_pressure"])
    strongest_buy = max([l for l in levels if l["type"] == "support"], key=lambda x: x["buy_pressure"])
    
    # Check if there is a massive imbalance
    insight = ""
    if int(strongest_sell["sell_pressure"]) > 85:
        insight = f"Massive sell wall detected near {strongest_sell['price']}. Expect heavy resistance and potential rejection."
    elif int(strongest_buy["buy_pressure"]) > 85:
        insight = f"Large liquidity cluster and buy pressure detected at {strongest_buy['price']}. Strong support zone established."
    else:
        insight = "Order book is relatively balanced. Watch for micro-structure shifts near current price."
        
    return {
        "instrument": instrument,
        "current_price": current_price,
        "levels": levels,
        "insight": insight,
        "strongest_support": strongest_buy['price'],
        "strongest_resistance": strongest_sell['price']
    }
