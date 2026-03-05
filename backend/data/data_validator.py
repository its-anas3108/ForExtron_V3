"""
data_validator.py – Data Integrity Agent helper.
Detects missing candles and abnormal price spikes.
"""

import logging
import pandas as pd
import numpy as np
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


class DataValidator:

    def __init__(self, spike_z_threshold: float = 4.0):
        self.spike_z_threshold = spike_z_threshold

    def validate(self, df: pd.DataFrame, timeframe_minutes: int = 5) -> dict:
        issues = []

        # Check for missing candles
        if "timestamp" in df.columns:
            ts = pd.to_datetime(df["timestamp"])
            expected_gap = pd.Timedelta(minutes=timeframe_minutes)
            gaps = ts.diff().dropna()
            large_gaps = gaps[gaps > expected_gap * 1.5]
            if not large_gaps.empty:
                issues.append({
                    "type": "missing_candles",
                    "count": len(large_gaps),
                    "largest_gap_minutes": large_gaps.max().total_seconds() / 60,
                })

        # Spike detection on close prices
        if "close" in df.columns and len(df) >= 10:
            returns = df["close"].pct_change().dropna()
            z_scores = (returns - returns.mean()) / (returns.std() + 1e-9)
            spikes = z_scores[z_scores.abs() > self.spike_z_threshold]
            if not spikes.empty:
                issues.append({
                    "type": "price_spike",
                    "count": len(spikes),
                    "max_z": float(spikes.abs().max()),
                })

        return {
            "valid": len(issues) == 0,
            "issues": issues,
            "candle_count": len(df),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
