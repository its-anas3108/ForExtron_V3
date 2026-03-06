"""
news_engine.py – AI News Impact Engine
Generates realistic, rotating Forex macro news events
with sentiment analysis and pair impact scoring.
"""

import random
import time
import hashlib
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any

# ── News Event Templates ─────────────────────────────────────────────────────
NEWS_TEMPLATES = [
    # Central Bank events
    {
        "category": "Central Bank",
        "headlines": [
            "Federal Reserve holds interest rates steady at {rate}%",
            "Fed Chair signals potential rate cut in upcoming meetings",
            "Federal Reserve raises rates by 25bps to {rate}%",
            "Fed minutes reveal hawkish stance on inflation",
            "Federal Reserve announces emergency liquidity measures",
        ],
        "source": "Federal Reserve",
        "base_pairs": {"EUR_USD": -1, "GBP_USD": -1, "USD_JPY": 1, "AUD_USD": -1, "USD_INR": 1, "EUR_INR": -1, "GBP_INR": -1},
        "impact_range": (65, 95),
    },
    {
        "category": "Central Bank",
        "headlines": [
            "ECB maintains key rate at {rate}%, signals patience",
            "ECB President hints at tightening cycle end",
            "European Central Bank cuts deposit rate by 25bps",
            "ECB surprises with hawkish forward guidance",
        ],
        "source": "European Central Bank",
        "base_pairs": {"EUR_USD": 1, "EUR_INR": 1, "GBP_USD": 0},
        "impact_range": (60, 90),
    },
    {
        "category": "Central Bank",
        "headlines": [
            "BOJ maintains ultra-loose monetary policy",
            "Bank of Japan hints at yield curve control adjustment",
            "BOJ Governor signals policy normalization ahead",
        ],
        "source": "Bank of Japan",
        "base_pairs": {"USD_JPY": -1, "EUR_USD": 0, "GBP_USD": 0},
        "impact_range": (55, 85),
    },
    {
        "category": "Central Bank",
        "headlines": [
            "RBI keeps repo rate unchanged at {rate}%",
            "Reserve Bank of India surprises with rate hike",
            "RBI Governor announces forex reserve intervention",
            "RBI eases capital flow restrictions for FPIs",
        ],
        "source": "Reserve Bank of India",
        "base_pairs": {"USD_INR": -1, "EUR_INR": -1, "GBP_INR": -1},
        "impact_range": (60, 88),
    },
    # Economic Data
    {
        "category": "Economic Data",
        "headlines": [
            "US Non-Farm Payrolls beat expectations at {value}K jobs",
            "NFP disappoints: only {value}K jobs added vs {expected}K expected",
            "US unemployment rate drops to {rate}%, labor market tight",
            "US jobs report shows mixed signals for Fed policy",
        ],
        "source": "Bureau of Labor Statistics",
        "base_pairs": {"EUR_USD": -1, "GBP_USD": -1, "USD_JPY": 1, "AUD_USD": -1, "USD_INR": 1},
        "impact_range": (70, 98),
    },
    {
        "category": "Economic Data",
        "headlines": [
            "US CPI rises {value}% YoY, above {expected}% forecast",
            "US inflation cools to {value}%, below expectations",
            "Core CPI surprises to the upside at {value}%",
            "US PPI signals easing pipeline inflation",
        ],
        "source": "Bureau of Labor Statistics",
        "base_pairs": {"EUR_USD": -1, "GBP_USD": -1, "USD_JPY": 1, "AUD_USD": -1, "USD_INR": 1},
        "impact_range": (72, 96),
    },
    {
        "category": "Economic Data",
        "headlines": [
            "Eurozone GDP growth surprises at {value}% QoQ",
            "German manufacturing PMI falls to {value}, contraction deepens",
            "Eurozone inflation drops to {value}%, ECB relieved",
        ],
        "source": "Eurostat",
        "base_pairs": {"EUR_USD": 1, "EUR_INR": 1},
        "impact_range": (50, 80),
    },
    {
        "category": "Economic Data",
        "headlines": [
            "India GDP growth accelerates to {value}% in Q3",
            "Indian trade deficit widens to ${value}B, INR under pressure",
            "India CPI inflation rises to {value}%, above RBI target",
        ],
        "source": "Ministry of Statistics",
        "base_pairs": {"USD_INR": 1, "EUR_INR": 1, "GBP_INR": 1},
        "impact_range": (55, 82),
    },
    # Geopolitical
    {
        "category": "Geopolitical",
        "headlines": [
            "Middle East tensions escalate, oil prices surge {value}%",
            "Trade negotiations between US and China resume",
            "EU imposes new sanctions, Euro volatility expected",
            "Global risk sentiment improves on ceasefire reports",
            "OPEC+ announces surprise production cut",
        ],
        "source": "Reuters",
        "base_pairs": {"EUR_USD": 0, "GBP_USD": 0, "USD_JPY": -1, "AUD_USD": -1, "USD_INR": 1},
        "impact_range": (40, 78),
    },
    # Market Sentiment
    {
        "category": "Market Sentiment",
        "headlines": [
            "US Dollar Index (DXY) breaks above {value} resistance",
            "Risk-on rally lifts commodity currencies across the board",
            "Safe-haven flows push JPY and CHF higher",
            "Carry trade unwind accelerates in Asian session",
            "Institutional positioning shifts to long USD",
        ],
        "source": "Market Analysis",
        "base_pairs": {"EUR_USD": -1, "GBP_USD": -1, "USD_JPY": 1, "AUD_USD": -1, "USD_INR": 1},
        "impact_range": (35, 70),
    },
]

# Cache for consistent news within a time window
_news_cache: Dict[str, Any] = {"events": [], "generated_at": 0}


def _generate_event(template: Dict, seed: int) -> Dict[str, Any]:
    """Generate a single news event from a template with consistent randomization."""
    rng = random.Random(seed)

    headline = rng.choice(template["headlines"])

    # Fill in template variables
    headline = headline.replace("{rate}", f"{rng.uniform(3.5, 6.5):.2f}")
    headline = headline.replace("{value}", f"{rng.uniform(0.5, 350):.1f}")
    headline = headline.replace("{expected}", f"{rng.uniform(0.5, 300):.1f}")

    # Determine sentiment based on pair impacts
    impacts = {}
    overall_direction = 0
    for pair, base_dir in template["base_pairs"].items():
        # Add some randomness to the impact direction
        noise = rng.uniform(-0.3, 0.3)
        actual_dir = base_dir + noise
        if abs(actual_dir) < 0.2:
            pair_sentiment = "neutral"
        elif actual_dir > 0:
            pair_sentiment = "bullish"
        else:
            pair_sentiment = "bearish"

        impact_score = rng.randint(*template["impact_range"])
        impacts[pair] = {
            "direction": pair_sentiment,
            "impact_score": impact_score,
        }
        overall_direction += actual_dir

    if overall_direction > 0.5:
        sentiment = "bullish"
    elif overall_direction < -0.5:
        sentiment = "bearish"
    else:
        sentiment = "neutral"

    # Timestamp: spread events across the last 2 hours
    minutes_ago = rng.randint(1, 120)
    event_time = datetime.now(timezone.utc) - timedelta(minutes=minutes_ago)

    return {
        "id": hashlib.md5(f"{seed}{headline}".encode()).hexdigest()[:12],
        "headline": headline,
        "source": template["source"],
        "category": template["category"],
        "sentiment": sentiment,
        "impact_score": rng.randint(*template["impact_range"]),
        "affected_pairs": impacts,
        "timestamp": event_time.isoformat(),
        "minutes_ago": minutes_ago,
    }


def get_news_feed(count: int = 10) -> List[Dict[str, Any]]:
    """Get the latest simulated news events. Regenerates every 60 seconds."""
    global _news_cache

    current_window = int(time.time() // 60)  # Changes every minute

    if _news_cache["generated_at"] != current_window:
        events = []
        base_seed = current_window * 1000

        # Pick random templates and generate events
        templates_pool = NEWS_TEMPLATES * 2  # Double the pool
        rng = random.Random(base_seed)
        selected = rng.sample(templates_pool, min(count + 3, len(templates_pool)))

        for i, template in enumerate(selected[:count]):
            event = _generate_event(template, base_seed + i)
            events.append(event)

        # Sort by recency
        events.sort(key=lambda e: e["minutes_ago"])

        _news_cache = {"events": events, "generated_at": current_window}

    return _news_cache["events"][:count]


def get_pair_news_impact(pair: str) -> Dict[str, Any]:
    """Get aggregated news impact for a specific currency pair."""
    events = get_news_feed(10)

    pair_events = []
    total_bullish = 0
    total_bearish = 0
    total_neutral = 0

    for event in events:
        if pair in event["affected_pairs"]:
            impact = event["affected_pairs"][pair]
            pair_events.append({
                "headline": event["headline"],
                "source": event["source"],
                "category": event["category"],
                "direction": impact["direction"],
                "impact_score": impact["impact_score"],
                "minutes_ago": event["minutes_ago"],
            })
            if impact["direction"] == "bullish":
                total_bullish += impact["impact_score"]
            elif impact["direction"] == "bearish":
                total_bearish += impact["impact_score"]
            else:
                total_neutral += impact["impact_score"]

    total = total_bullish + total_bearish + total_neutral
    if total > 0:
        bullish_pct = round(total_bullish / total * 100, 1)
        bearish_pct = round(total_bearish / total * 100, 1)
        neutral_pct = round(total_neutral / total * 100, 1)
    else:
        bullish_pct = bearish_pct = neutral_pct = 33.3

    if total_bullish > total_bearish * 1.3:
        net_sentiment = "bullish"
    elif total_bearish > total_bullish * 1.3:
        net_sentiment = "bearish"
    else:
        net_sentiment = "neutral"

    return {
        "pair": pair,
        "net_sentiment": net_sentiment,
        "bullish_score": bullish_pct,
        "bearish_score": bearish_pct,
        "neutral_score": neutral_pct,
        "event_count": len(pair_events),
        "events": pair_events,
    }
