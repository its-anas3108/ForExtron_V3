"""
news_engine.py – Live Real-Time Macro News Engine
Fetches live macroeconomic events from Finnhub or Forex Factory,
parses the data, and maps it to AI trading insights for the dashboard.
"""

import time
import hashlib
import requests
import logging
import asyncio
from datetime import datetime, timezone
from typing import Dict, List, Any

import os
from chatbot.llm_engine import generate_llm_text

logger = logging.getLogger(__name__)

FINNHUB_API_KEY = os.getenv("FINNHUB_API_KEY", "")  # Need to set this in environment
FINNHUB_NEWS_URL = "https://finnhub.io/api/v1/news"
FF_CALENDAR_URL = "https://nfs.faireconomy.media/ff_calendar_thisweek.json"

# Cache for 15 minutes to avoid rate limits
_news_cache: Dict[str, Any] = {"events": [], "last_fetched": 0}
CACHE_TTL = 900  # 15 minutes

# Mappings from Country to typical FX pairs
COUNTRY_PAIR_MAP = {
    "USD": [("EUR_USD", -1), ("GBP_USD", -1), ("USD_JPY", 1), ("AUD_USD", -1), ("USD_INR", 1)],
    "EUR": [("EUR_USD", 1), ("EUR_INR", 1)],
    "GBP": [("GBP_USD", 1), ("GBP_INR", 1)],
    "JPY": [("USD_JPY", -1)],
    "AUD": [("AUD_USD", 1)],
    "CAD": [("USD_CAD", -1)],
    "CHF": [("USD_CHF", -1)],
    "NZD": [("NZD_USD", 1)],
    "CNY": [("USD_JPY", 1), ("AUD_USD", 1)],  # Proxies
}

def _parse_ff_date(date_str: str) -> datetime:
    try:
        return datetime.fromisoformat(date_str)
    except Exception:
        return datetime.now(timezone.utc)

def _determine_sentiment(text: str) -> str:
    text = text.lower()
    bullish_words = ["surge", "jump", "rise", "soar", "gain", "high", "positive", "beat", "up"]
    bearish_words = ["drop", "fall", "plunge", "decline", "low", "negative", "miss", "down", "cut"]
    
    bull_score = sum(1 for w in bullish_words if w in text)
    bear_score = sum(1 for w in bearish_words if w in text)
    
    if bull_score > bear_score:
        return "bullish"
    elif bear_score > bull_score:
        return "bearish"
    return "neutral"

async def _analyze_contribution(headline: str, summary: str, sentiment: str) -> str:
    if sentiment == "neutral":
        return ""
    try:
        prompt = f"Analyze this Forex news securely: '{headline} - {summary}'. In exactly one short sentence, explain WHY this is fundamentally {sentiment.upper()} for the relevant currency. Do not use jargon. Start immediately with the reason."
        content = await generate_llm_text(prompt)
        return content or "Affects macro supply/demand directly."
    except Exception as e:
        logger.error(f"News LLM parsing error: {e}")
        return "Affects macro supply/demand directly."

async def fetch_live_news() -> List[Dict[str, Any]]:
    """Fetches and processes live forex news from Finnhub, Forex Factory, or synthetic fallback."""
    global _news_cache
    now = time.time()
    
    if now - _news_cache["last_fetched"] < CACHE_TTL and _news_cache["events"]:
        return _news_cache["events"]

    # ── Try Finnhub first ────────────────────────────────────────────────────
    if FINNHUB_API_KEY:
        try:
            processed_events = await _fetch_finnhub_news(now)
            if processed_events:
                return processed_events
        except Exception as e:
            logger.error(f"Finnhub fetch failed: {e}")

    # ── Fallback to Forex Factory RSS ────────────────────────────────────────
    try:
        processed_events = await _fetch_forex_factory_news(now)
        if processed_events:
            return processed_events
    except Exception as e:
        logger.error(f"Forex Factory fallback failed: {e}")

    # ── Final fallback: synthetic AI news ────────────────────────────────────
    logger.info("📡 No live news available, using synthetic intelligence fallback.")
    synthetic = await _get_synthetic_news()
    _news_cache["events"] = synthetic
    _news_cache["last_fetched"] = now
    return synthetic


async def _fetch_finnhub_news(now_timestamp: float) -> List[Dict[str, Any]]:
    """Fetches and processes news from Finnhub.io."""
    global _news_cache

    params = {"category": "forex", "token": FINNHUB_API_KEY}
    resp = requests.get(FINNHUB_NEWS_URL, params=params, timeout=10)
    resp.raise_for_status()
    data = resp.json()

    current_time = datetime.now(timezone.utc)
    processed_events = []
    
    for item in data:
        event_ts = item.get("datetime", now_timestamp)
        event_time = datetime.fromtimestamp(event_ts, tz=timezone.utc)
        
        delta = current_time - event_time
        minutes_ago = int(delta.total_seconds() / 60)
        
        if minutes_ago < 0:
            continue
            
        headline = item.get("headline", "")
        summary = item.get("summary", "")
        source = item.get("source", "Finnhub")
        
        sentiment = _determine_sentiment(headline + " " + summary)
        
        # Skip neutral news
        if sentiment == "neutral":
            continue
            
        impact_score = 60 if sentiment == "bullish" else 80

        related = item.get("related", "")
        affected_pairs = {}
        
        if related:
            for symbol in related.split(","):
                sym = symbol.strip().upper()
                if len(sym) >= 3:
                    pair_name = f"{sym}_USD"
                    affected_pairs[pair_name] = {
                        "direction": sentiment,
                        "impact_score": impact_score
                    }
                    
        if not affected_pairs:
            affected_pairs["GLOBAL_FX"] = {
                "direction": sentiment,
                "impact_score": impact_score
            }
            
        processed_events.append({
            "id": str(item.get("id", hashlib.md5(headline.encode()).hexdigest()[:12])),
            "headline": headline,
            "summary": summary,
            "source": source,
            "category": "Live Forex News",
            "sentiment": sentiment,
            "impact_score": impact_score,
            "affected_pairs": affected_pairs,
            "timestamp": event_time.isoformat(),
            "minutes_ago": minutes_ago
        })

    # Sort by most recent
    processed_events.sort(key=lambda x: x["minutes_ago"])

    # Run LLM contributions on top 5 events
    llm_tasks = []
    for ev in processed_events[:5]:
        llm_tasks.append(_analyze_contribution(ev["headline"], ev.get("summary", ""), ev["sentiment"]))
    
    if llm_tasks:
        contributions = await asyncio.gather(*llm_tasks)
        for i, contrib in enumerate(contributions):
            processed_events[i]["contribution"] = contrib
    
    if processed_events:
        _news_cache["events"] = processed_events
        _news_cache["last_fetched"] = now_timestamp
        
    return processed_events


async def _fetch_forex_factory_news(now_timestamp: float) -> List[Dict[str, Any]]:
    """Fallback parser using Forex Factory calendar feed."""
    global _news_cache
    
    resp = requests.get(FF_CALENDAR_URL, timeout=10)
    resp.raise_for_status()
    data = resp.json()

    current_time = datetime.now(timezone.utc)
    processed_events = []
    
    for item in data:
        country = item.get("country", "")
        impact_str = item.get("impact", "Low")
        event_time = _parse_ff_date(item.get("date", ""))
        
        delta = current_time - event_time
        minutes_ago = int(delta.total_seconds() / 60)
        
        if minutes_ago < 0:
            continue
            
        headline = item.get("title", "")
        summary = item.get("description", "") or ""
        impact_score = 85 if impact_str == "High" else 65 if impact_str == "Medium" else 40
        
        forecast = item.get("forecast", "")
        previous = item.get("previous", "")
        sentiment = "neutral"
        net_dir = 0
        if forecast and previous:
            try:
                f_cln = forecast.replace('%', '').replace('K', '').replace('B', '').replace('M', '').replace(',', '')
                p_cln = previous.replace('%', '').replace('K', '').replace('B', '').replace('M', '').replace(',', '')
                if float(f_cln) > float(p_cln):
                    sentiment, net_dir = "bullish", 1
                elif float(f_cln) < float(p_cln):
                    sentiment, net_dir = "bearish", -1
            except Exception:
                pass
                
        # Skip neutral news
        if sentiment == "neutral":
            continue

        affected_pairs = {}
        for pair, multiplier in COUNTRY_PAIR_MAP.get(country, []):
            pair_dir = net_dir * multiplier
            p_s = "bullish" if pair_dir > 0 else "bearish" if pair_dir < 0 else "neutral"
            affected_pairs[pair] = {"direction": p_s, "impact_score": impact_score if p_s != "neutral" else 10}
            
        processed_events.append({
            "id": hashlib.md5(f"{headline}{event_time}".encode()).hexdigest()[:12],
            "headline": headline,
            "summary": summary,
            "source": "Forex Factory RSS",
            "category": f"Macro {country} Event",
            "sentiment": sentiment,
            "impact_score": impact_score,
            "affected_pairs": affected_pairs,
            "timestamp": event_time.isoformat(),
            "minutes_ago": minutes_ago
        })

    # Sort by most recent
    processed_events.sort(key=lambda x: x["minutes_ago"])

    # Run LLM contributions on top 5 events
    llm_tasks = []
    for ev in processed_events[:5]:
        llm_tasks.append(_analyze_contribution(ev["headline"], ev.get("summary", ""), ev["sentiment"]))
    
    if llm_tasks:
        contributions = await asyncio.gather(*llm_tasks)
        for i, contrib in enumerate(contributions):
            processed_events[i]["contribution"] = contrib

    if processed_events:
        _news_cache["events"] = processed_events
        _news_cache["last_fetched"] = now_timestamp
        
    return processed_events


async def _get_synthetic_news() -> List[Dict[str, Any]]:
    """Generates high-quality institutional mock news for the dashboard."""
    from datetime import datetime, timedelta, timezone
    import uuid
    
    current_time = datetime.now(timezone.utc)
    
    headlines = [
        ("Federal Reserve Officials Signal Caution on Path of Rate Cuts", "Central Bank", "bearish", ["EUR_USD", "USD_JPY", "USD_INR"]),
        ("ECB's Lagarde Highlights Persistence of Service Sector Inflation", "Central Bank", "bullish", ["EUR_USD", "EUR_INR"]),
        ("UK Retail Sales Beat Expectations, Fueling BOE Hawkish Bets", "Economic Data", "bullish", ["GBP_USD", "GBP_INR"]),
        ("Global Equity Markets Retreat as Geopolitical Tensions Escalate", "Geopolitical", "bearish", ["AUD_USD", "NZD_USD", "USD_JPY"]),
        ("Commodity Prices Surge Amid Supply Side Constraints in Energy", "Economic Data", "bullish", ["USD_CAD", "AUD_USD"]),
        ("Bank of Japan Weighs Further Policy Normalization as Wages Rise", "Central Bank", "bullish", ["USD_JPY"]),
        ("US Manufacturing Activity Hits 18-Month High in Flash PMIs", "Economic Data", "bullish", ["EUR_USD", "USD_JPY", "USD_INR"]),
        ("Eurozone Growth Outlook Dims as Industrial Orders Decline", "Economic Data", "bearish", ["EUR_USD", "EUR_INR"]),
        ("Treasury Yields Stabilize as Investors Await Next Inflation Print", "Market Sentiment", "neutral", ["EUR_USD", "USD_JPY"]),
        ("Safe-Haven Demand Propels Gold and Yen to Key Resistance Levels", "Market Sentiment", "bearish", ["USD_JPY", "GBP_USD"]),
    ]
    
    synthetic_events = []
    for i, (headline, cat, sent, pairs) in enumerate(headlines):
        # Stagger timestamps within the last 24 hours
        ts = current_time - timedelta(minutes=i * 45 + 10)
        
        affected = {}
        impact = 75 if i < 3 else 55
        for p in pairs:
            direction = sent
            if p.startswith("USD_") and sent == "bullish": direction = "bearish"
            if p.endswith("_USD") and sent == "bullish": direction = "bearish"
            elif p.endswith("_USD") and sent == "bearish": direction = "bullish"
            
            affected[p] = {"direction": direction, "impact_score": impact}

        synthetic_events.append({
            "id": f"syn-{uuid.uuid4().hex[:8]}",
            "headline": headline,
            "source": "ForeXtron Intelligence",
            "category": cat,
            "sentiment": sent,
            "impact_score": impact,
            "affected_pairs": affected,
            "timestamp": ts.isoformat(),
            "minutes_ago": i * 45 + 10,
            "contribution": f"Synthetic AI analysis: This {cat} event shifts sentiment to {sent} for affected tokens."
        })
        
    return synthetic_events

async def get_news_feed(limit: int = 10) -> List[Dict[str, Any]]:
    """Returns the latest 'limit' news events, filtered to Forex."""
    events = await fetch_live_news()
    return events[:limit]


async def get_pair_news_impact(pair: str) -> Dict[str, Any]:
    """Calculates cumulative impact of recent news for a specific pair."""
    events = await fetch_live_news()
    
    pair_events = []
    total_bullish = 0
    total_bearish = 0
    total_neutral = 0

    # Consider the last 30 events for aggregated impact
    for event in events[:30]:
        if pair in event.get("affected_pairs", {}):
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
        "events": pair_events[:10],
    }
