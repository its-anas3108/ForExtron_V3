"""
news_engine.py – Live Real-Time Macro News Engine
Fetches live macroeconomic events from Forex Factory's public JSON feed,
parses the data, and maps it to AI trading insights for the dashboard.
"""

import time
import hashlib
import requests
import logging
from datetime import datetime, timezone
from typing import Dict, List, Any

import os

import os

logger = logging.getLogger(__name__)

FINNHUB_API_KEY = os.getenv("FINNHUB_API_KEY", "") # Need to set this in environment
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
    "CNY": [("USD_JPY", 1), ("AUD_USD", 1)], # Proxies
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

def fetch_live_news() -> List[Dict[str, Any]]:
    """Fetches and processes live forex news from Finnhub.io."""
    global _news_cache
    now = time.time()
    
    if now - _news_cache["last_fetched"] < CACHE_TTL and _news_cache["events"]:
        return _news_cache["events"]

    if not FINNHUB_API_KEY:
        logger.warning("FINNHUB_API_KEY is not set. Falling back to Forex Factory RSS.")
        return fetch_fallback_news(now)

    try:
        # Finnhub specifically has a forex category
        params = {"category": "forex", "token": FINNHUB_API_KEY}
        resp = requests.get(FINNHUB_NEWS_URL, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        logger.error(f"Failed to fetch Finnhub news: {e}")
        return _news_cache["events"]

    current_time = datetime.now(timezone.utc)
    processed_events = []
    
    for item in data:
        # Finnhub time is UNIX timestamp
        event_ts = item.get("datetime", now)
        event_time = datetime.fromtimestamp(event_ts, tz=timezone.utc)
        
        delta = current_time - event_time
        minutes_ago = int(delta.total_seconds() / 60)
        
        # Only show events from today, skip negative (future)
        if minutes_ago < 0:
            continue
            
        headline = item.get("headline", "")
        summary = item.get("summary", "")
        source = item.get("source", "Finnhub")
        
        # Analyze sentiment
        sentiment = _determine_sentiment(headline + " " + summary)
        
        # USER REQUEST: "dont show neutral news"
        if sentiment == "neutral":
            continue
            
        impact_score = 60 if sentiment == "bullish" else 80  # Heuristic

        # Finnhub related field usually contains pairs/symbols like "EUR,USD"
        related = item.get("related", "")
        affected_pairs = {}
        
        if related:
            # Simple heuristic mapping based on related
            for symbol in related.split(","):
                sym = symbol.strip().upper()
                if len(sym) >= 3:
                    pair_name = f"{sym}_USD" # Default to USD pair assumption for tagging
                    affected_pairs[pair_name] = {
                        "direction": sentiment,
                        "impact_score": impact_score
                    }
                    
        # If no explicit pairs found, make it a general macro impact
        if not affected_pairs:
            affected_pairs["GLOBAL_FX"] = {
                "direction": sentiment,
                "impact_score": impact_score
            }
            
        processed_events.append({
            "id": str(item.get("id", hashlib.md5(headline.encode()).hexdigest()[:12])),
            "headline": headline,
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
    
    _news_cache["events"] = processed_events
    _news_cache["last_fetched"] = now
    
    return processed_events

def fetch_fallback_news(now_timestamp: float) -> List[Dict[str, Any]]:
    """Fallback parser if Finnhub Key is missing."""
    global _news_cache
    try:
        resp = requests.get(FF_CALENDAR_URL, timeout=10)
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        logger.error(f"Fallback parse failed: {e}")
        return _news_cache["events"]

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
                
        # Skip neutral fallback news per user request
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
            "source": "Forex Factory RSS",
            "category": f"Macro {country} Event",
            "sentiment": sentiment,
            "impact_score": impact_score,
            "affected_pairs": affected_pairs,
            "timestamp": event_time.isoformat(),
            "minutes_ago": minutes_ago
        })

    processed_events.sort(key=lambda x: x["minutes_ago"])
    _news_cache["events"] = processed_events
    _news_cache["last_fetched"] = now_timestamp
    return processed_events

def get_news_feed(count: int = 10) -> List[Dict[str, Any]]:
    events = fetch_live_news()
    return events[:count]

def get_pair_news_impact(pair: str) -> Dict[str, Any]:
    events = fetch_live_news()
    
    pair_events = []
    total_bullish = 0
    total_bearish = 0
    total_neutral = 0

    # Consider the last 30 events for aggregated impact
    for event in events[:30]:
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

    # Only return the most recent 10 specific for the pair to the UI
    return {
        "pair": pair,
        "net_sentiment": net_sentiment,
        "bullish_score": bullish_pct,
        "bearish_score": bearish_pct,
        "neutral_score": neutral_pct,
        "event_count": len(pair_events),
        "events": pair_events[:10],
    }
