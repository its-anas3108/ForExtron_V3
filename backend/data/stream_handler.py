"""
stream_handler.py – Converts OANDA tick stream into closed M5 candles,
stores them in MongoDB, and triggers the full analysis pipeline.
"""

import asyncio
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Optional
import pandas as pd

from app.config import settings
from app.websocket_manager import manager
from data.oanda_client import oanda
from database.crud import insert_candle, get_recent_candles
from features.indicators import compute_indicators
from features.structure_engine import StructureEngine
from features.regime_features import compute_regime_features

logger = logging.getLogger(__name__)


class CandleBuilder:
    """Builds OHLCV candles from raw tick data for a specific timeframe."""

    def __init__(self, instrument: str, timeframe_minutes: int = 5):
        self.instrument = instrument
        self.tf_minutes = timeframe_minutes
        self.reset()

    def reset(self):
        self.open = self.high = self.low = self.close = 0.0
        self.volume = 0
        self.start_time: Optional[datetime] = None

    def _candle_start(self, tick_time: datetime) -> datetime:
        """Floor tick time to the nearest candle boundary."""
        minutes = (tick_time.minute // self.tf_minutes) * self.tf_minutes
        return tick_time.replace(minute=minutes, second=0, microsecond=0)

    def update(self, tick: dict) -> Optional[dict]:
        """Feed a tick into the builder. Returns a closed candle dict or None."""
        mid = (tick["bid"] + tick["ask"]) / 2
        tick_time = pd.Timestamp(tick["time"]).to_pydatetime().replace(tzinfo=timezone.utc)
        candle_start = self._candle_start(tick_time)

        # New candle period?
        if self.start_time is None:
            self.start_time = candle_start
            self.open = self.high = self.low = self.close = mid

        if candle_start > self.start_time:
            # Close the previous candle
            closed = {
                "pair": self.instrument,
                "timeframe": f"M{self.tf_minutes}",
                "timestamp": self.start_time.isoformat(),
                "open": round(self.open, 5),
                "high": round(self.high, 5),
                "low": round(self.low, 5),
                "close": round(self.close, 5),
                "volume": self.volume,
            }
            # Start new candle
            self.start_time = candle_start
            self.open = self.high = self.low = self.close = mid
            self.volume = 1
            return closed

        # Continue current candle
        self.high = max(self.high, mid)
        self.low = min(self.low, mid)
        self.close = mid
        self.volume += 1
        return None


class StreamHandler:
    """
    Manages live price streaming for all supported instruments.
    For INR pairs (USD_INR, EUR_INR, GBP_INR), uses HTTP polling fallback
    since OANDA streaming may have reduced tick frequency.
    """

    STANDARD_INSTRUMENTS = ["EUR_USD", "GBP_USD", "USD_JPY", "AUD_USD", "USD_CHF", "USD_CAD", "NZD_USD"]
    INR_INSTRUMENTS = ["USD_INR", "EUR_INR", "GBP_INR"]
    # Poll interval for INR pairs (seconds)
    INR_POLL_INTERVAL = 10

    def __init__(self):
        self.builders: Dict[str, CandleBuilder] = {}
        self.running = False
        self._active_instrument: Optional[str] = None
        self.structure_engine = StructureEngine()
        # Dedicated thread pool for streaming so it doesn't block the default executor
        from concurrent.futures import ThreadPoolExecutor
        self._stream_executor = ThreadPoolExecutor(max_workers=3, thread_name_prefix="oanda-stream")

    async def start(self, instrument: str):
        self.running = True
        self._active_instrument = instrument
        self.builders[instrument] = CandleBuilder(instrument)

        # Seed history first so the UI isn't blank
        await self._seed_history(instrument)

        if instrument in self.INR_INSTRUMENTS:
            await self._poll_inr(instrument)
        else:
            await self._stream_standard(instrument)

    async def _seed_history(self, instrument: str):
        """Fetch last 200 candles from OANDA on startup to populate DB."""
        try:
            logger.info(f"🌱 Seeding history for {instrument}...")
            # Use singleton oanda client
            history = await asyncio.get_event_loop().run_in_executor(
                self._stream_executor, lambda: oanda.get_historical_candles(instrument, count=200)
            )
            for candle in history:
                await insert_candle(candle)
            logger.info(f"✅ Seeded {len(history)} candles for {instrument}")
        except Exception as e:
            logger.error(f"Failed to seed history for {instrument}: {e}")

    async def stop(self):
        self.running = False

    # ── Standard streaming (non-INR) ─────────────────────────────────────────
    async def _stream_standard(self, instrument: str):
        logger.info(f"📡 Starting tick stream for {instrument}")
        loop = asyncio.get_event_loop()

        def _blocking_stream():
            try:
                for tick in oanda.stream_prices([instrument]):
                    if not self.running:
                        break
                    asyncio.run_coroutine_threadsafe(self._handle_tick(instrument, tick), loop)
            except Exception as e:
                logger.error(f"Stream error for {instrument}: {e}", exc_info=True)

        await loop.run_in_executor(self._stream_executor, _blocking_stream)

    # ── INR polling fallback ──────────────────────────────────────────────────
    async def _poll_inr(self, instrument: str):
        logger.info(f"🔄 Starting poll-based feed for INR pair: {instrument}")
        while self.running:
            try:
                price = await asyncio.get_event_loop().run_in_executor(
                    self._stream_executor, lambda: oanda.get_latest_price(instrument)
                )
                await self._handle_tick(instrument, price)
            except Exception as e:
                logger.warning(f"INR poll error for {instrument}: {e}")
            await asyncio.sleep(self.INR_POLL_INTERVAL)

    # ── Tick handler → candle builder → pipeline ──────────────────────────────
    async def _handle_tick(self, instrument: str, tick: dict):
        builder = self.builders.get(instrument)
        if not builder:
            return

        closed = builder.update(tick)
        if closed:
            await self._process_closed_candle(instrument, closed)

    async def _process_closed_candle(self, instrument: str, candle: dict):
        """Full pipeline: store → broadcast → features → regime → models → signal."""
        try:
            # 1. Persist raw candle
            await insert_candle(candle)

            # 2. Broadcast live candle to WebSocket clients immediately
            await manager.broadcast_candle(instrument, candle)

            # 3. Fetch recent candles for feature computation
            recent = await get_recent_candles(instrument, limit=settings.LOOKBACK_CANDLES + 10)
            if len(recent) < 20:
                return  # Not enough data for indicators

            df = pd.DataFrame(recent)
            df = compute_indicators(df)
            df = compute_regime_features(df)
            df = self.structure_engine.compute(df)

            # 4. Trigger full analysis pipeline (import here to avoid circular)
            from decision.decision_engine import DecisionEngine
            engine = DecisionEngine()
            signal = await engine.evaluate(instrument, df)

            if signal:
                await manager.broadcast_signal(instrument, signal)

            logger.debug(f"✅ Candle processed for {instrument}: {candle['timestamp']}")

        except Exception as e:
            logger.error(f"Pipeline error for {instrument}: {e}", exc_info=True)
