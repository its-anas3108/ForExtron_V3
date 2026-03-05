"""
oanda_client.py – OANDA REST v20 API wrapper
Handles historical candles, streaming prices, account info and order placement.
"""

import requests
import json
import logging
from datetime import datetime, timezone
from typing import List, Optional, Generator
from app.config import settings

logger = logging.getLogger(__name__)

OANDA_TIMEFRAME_MAP = {
    "M1": "M1", "M5": "M5", "M15": "M15", "M30": "M30",
    "H1": "H1", "H4": "H4", "D": "D",
}


class OandaClient:
    """Synchronous OANDA REST v20 client."""

    def __init__(self):
        self.base_url = settings.OANDA_BASE_URL
        self.stream_url = settings.OANDA_STREAM_URL
        self.account_id = settings.OANDA_ACCOUNT_ID
        self.headers = {
            "Authorization": f"Bearer {settings.OANDA_API_KEY}",
            "Content-Type": "application/json",
        }

    # ── Account ───────────────────────────────────────────────────────────────
    def get_account_summary(self) -> dict:
        url = f"{self.base_url}/v3/accounts/{self.account_id}/summary"
        resp = requests.get(url, headers=self.headers, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        account = data["account"]
        return {
            "balance": float(account.get("balance", 0)),
            "nav": float(account.get("NAV", 0)),
            "unrealized_pl": float(account.get("unrealizedPL", 0)),
            "margin_used": float(account.get("marginUsed", 0)),
            "open_trade_count": int(account.get("openTradeCount", 0)),
            "currency": account.get("currency", "USD"),
        }

    # ── Historical Candles ────────────────────────────────────────────────────
    def get_historical_candles(
        self,
        instrument: str,
        granularity: str = "M5",
        count: int = 200,
        from_time: Optional[str] = None,
        to_time: Optional[str] = None,
    ) -> List[dict]:
        url = f"{self.base_url}/v3/instruments/{instrument}/candles"
        params = {
            "granularity": OANDA_TIMEFRAME_MAP.get(granularity, "M5"),
            "price": "M",  # Mid candles
        }
        if from_time and to_time:
            params["from"] = from_time
            params["to"] = to_time
        else:
            params["count"] = count

        resp = requests.get(url, headers=self.headers, params=params, timeout=15)
        resp.raise_for_status()
        raw = resp.json().get("candles", [])

        candles = []
        for c in raw:
            if not c.get("complete", False):
                continue
            mid = c.get("mid", {})
            candles.append({
                "pair": instrument,
                "timeframe": granularity,
                "timestamp": c["time"],
                "open": float(mid.get("o", 0)),
                "high": float(mid.get("h", 0)),
                "low": float(mid.get("l", 0)),
                "close": float(mid.get("c", 0)),
                "volume": int(c.get("volume", 0)),
            })
        return candles

    # ── INR-specific candle fetcher (same as above, just convenience wrapper) ─
    def get_inr_candles(self, instrument: str = "USD_INR", count: int = 200) -> List[dict]:
        """Shortcut for INR pairs (USD_INR, EUR_INR, GBP_INR)."""
        return self.get_historical_candles(instrument=instrument, granularity="M5", count=count)

    # ── Latest Price ──────────────────────────────────────────────────────────
    def get_latest_price(self, instrument: str) -> dict:
        url = f"{self.base_url}/v3/accounts/{self.account_id}/pricing"
        params = {"instruments": instrument}
        resp = requests.get(url, headers=self.headers, params=params, timeout=10)
        resp.raise_for_status()
        prices = resp.json().get("prices", [{}])
        p = prices[0] if prices else {}
        return {
            "instrument": instrument,
            "bid": float(p.get("bids", [{}])[0].get("price", 0)),
            "ask": float(p.get("asks", [{}])[0].get("price", 0)),
            "time": p.get("time", ""),
        }

    # ── Streaming Price Generator ──────────────────────────────────────────────
    def stream_prices(self, instruments: List[str]) -> Generator[dict, None, None]:
        """Generator that yields tick dicts from the OANDA streaming endpoint."""
        url = f"{self.stream_url}/v3/accounts/{self.account_id}/pricing/stream"
        params = {"instruments": ",".join(instruments)}
        with requests.get(
            url, headers=self.headers, params=params, stream=True, timeout=30
        ) as resp:
            resp.raise_for_status()
            for line in resp.iter_lines():
                if line:
                    try:
                        tick = json.loads(line.decode("utf-8"))
                        if tick.get("type") == "PRICE":
                            yield {
                                "instrument": tick["instrument"],
                                "bid": float(tick["bids"][0]["price"]),
                                "ask": float(tick["asks"][0]["price"]),
                                "time": tick["time"],
                            }
                    except (json.JSONDecodeError, KeyError):
                        continue

    # ── Order Placement (Execution Gateway) ───────────────────────────────────
    def place_market_order(
        self,
        instrument: str,
        units: int,
        stop_loss: float,
        take_profit: float,
    ) -> dict:
        """Place a market order on OANDA (requires manual confirmation upstream)."""
        url = f"{self.base_url}/v3/accounts/{self.account_id}/orders"
        payload = {
            "order": {
                "type": "MARKET",
                "instrument": instrument,
                "units": str(units),
                "stopLossOnFill": {"price": f"{stop_loss:.5f}"},
                "takeProfitOnFill": {"price": f"{take_profit:.5f}"},
                "timeInForce": "FOK",
            }
        }
        resp = requests.post(url, headers=self.headers, json=payload, timeout=10)
        resp.raise_for_status()
        return resp.json()

    def close_trade(self, trade_id: str) -> dict:
        url = f"{self.base_url}/v3/accounts/{self.account_id}/trades/{trade_id}/close"
        resp = requests.put(url, headers=self.headers, timeout=10)
        resp.raise_for_status()
        return resp.json()


# Singleton instance
oanda = OandaClient()
