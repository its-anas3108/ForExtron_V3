"""
structure_engine.py – Institutional Market Structure Detection.

Detects:
  1. Break of Structure (BoS)
  2. Change of Character (ChoCH)
  3. Liquidity Sweep
  4. Higher High / Lower Low encoding
  5. Impulse Strength Ratio
  6. Structure Slope Index
  7. Order Block Detection
  8. Fair Value Gap (FVG)

All outputs are numeric features suitable for ML input.
"""

import pandas as pd
import numpy as np
from app.config import settings


class StructureEngine:
    """
    Computes institutional market structure features.
    All methods return numeric columns added to the same DataFrame.
    """

    def __init__(self, lookback: int = None):
        self.lookback = lookback or settings.STRUCTURE_LOOKBACK

    def compute(self, df: pd.DataFrame) -> pd.DataFrame:
        """Run the full structure pipeline."""
        df = df.copy()
        df = self._compute_swing_points(df)
        df = self._compute_hh_ll_encoding(df)
        df = self._compute_bos(df)
        df = self._compute_choch(df)
        df = self._compute_liquidity_sweep(df)
        df = self._compute_impulse_ratio(df)
        df = self._compute_structure_slope(df)
        df = self._compute_order_blocks(df)
        df = self._compute_fvg(df)
        df = df.fillna(0)
        return df

    # ── 1. Swing Points ───────────────────────────────────────────────────────
    def _compute_swing_points(self, df: pd.DataFrame, window: int = 5) -> pd.DataFrame:
        """Detect local swing highs and lows."""
        highs = df["high"].values
        lows = df["low"].values
        n = len(df)
        swing_high = np.zeros(n)
        swing_low = np.zeros(n)

        for i in range(window, n - window):
            if highs[i] == max(highs[i - window: i + window + 1]):
                swing_high[i] = highs[i]
            if lows[i] == min(lows[i - window: i + window + 1]):
                swing_low[i] = lows[i]

        df["swing_high"] = swing_high
        df["swing_low"] = swing_low
        return df

    # ── 2. HH / LL Encoding ──────────────────────────────────────────────────
    def _compute_hh_ll_encoding(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Encode trend direction as a rolling numerical score.
        +1 for each HH, -1 for each LL, 0 otherwise.
        Cumulative sum gives trend bias.
        """
        sh = df["swing_high"].values
        sl = df["swing_low"].values
        n = len(df)
        scores = np.zeros(n)
        last_sh = 0.0
        last_sl = np.inf

        for i in range(n):
            if sh[i] > 0:
                if sh[i] > last_sh:
                    scores[i] = 1   # Higher High
                elif sh[i] < last_sh:
                    scores[i] = -0.5  # Lower High (bearish signal)
                last_sh = sh[i]
            if sl[i] > 0:
                if sl[i] < last_sl:
                    scores[i] -= 1   # Lower Low
                elif sl[i] > last_sl:
                    scores[i] += 0.5  # Higher Low (bullish signal)
                last_sl = sl[i]

        df["hh_ll_score"] = scores
        df["trend_bias"] = pd.Series(scores).rolling(self.lookback).sum().values
        return df

    # ── 3. Break of Structure ─────────────────────────────────────────────────
    def _compute_bos(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        BoS detected when close breaks above the last significant swing high (bullish BoS)
        or breaks below the last significant swing low (bearish BoS).
        """
        n = len(df)
        bos_bull = np.zeros(n)
        bos_bear = np.zeros(n)
        last_sh = 0.0
        last_sl = np.inf

        for i in range(1, n):
            if df["swing_high"].iloc[i - 1] > 0:
                last_sh = df["swing_high"].iloc[i - 1]
            if df["swing_low"].iloc[i - 1] > 0:
                last_sl = df["swing_low"].iloc[i - 1]

            close = df["close"].iloc[i]
            if last_sh > 0 and close > last_sh:
                bos_bull[i] = 1
            if last_sl < np.inf and close < last_sl:
                bos_bear[i] = 1

        df["bos_bullish"] = bos_bull
        df["bos_bearish"] = bos_bear
        df["bos_net"] = bos_bull - bos_bear
        return df

    # ── 4. Change of Character ────────────────────────────────────────────────
    def _compute_choch(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        ChoCH: first BoS in the opposite direction after a sustained trend.
        Indicates a potential trend reversal.
        """
        n = len(df)
        choch = np.zeros(n)
        in_bull_trend = False
        in_bear_trend = False

        for i in range(self.lookback, n):
            recent_bull_bos = df["bos_bullish"].iloc[i - self.lookback: i].sum()
            recent_bear_bos = df["bos_bearish"].iloc[i - self.lookback: i].sum()

            if recent_bull_bos >= 2:
                in_bull_trend = True
                in_bear_trend = False
            if recent_bear_bos >= 2:
                in_bear_trend = True
                in_bull_trend = False

            if in_bull_trend and df["bos_bearish"].iloc[i] == 1:
                choch[i] = -1   # Bearish ChoCH (reversal signal)
                in_bull_trend = False
            elif in_bear_trend and df["bos_bullish"].iloc[i] == 1:
                choch[i] = 1    # Bullish ChoCH
                in_bear_trend = False

        df["choch"] = choch
        return df

    # ── 5. Liquidity Sweep ────────────────────────────────────────────────────
    def _compute_liquidity_sweep(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Liquidity sweep: wick extends beyond prior swing high/low but CLOSES back inside.
        Classic stop-hunt pattern used by institutional traders.
        """
        n = len(df)
        liq_sweep_high = np.zeros(n)
        liq_sweep_low = np.zeros(n)

        for i in range(self.lookback, n):
            window = df.iloc[i - self.lookback: i]
            prior_high = window["high"].max()
            prior_low = window["low"].min()

            row = df.iloc[i]
            # Wick above prior high but closed inside
            if row["high"] > prior_high and row["close"] < prior_high:
                liq_sweep_high[i] = 1
            # Wick below prior low but closed inside
            if row["low"] < prior_low and row["close"] > prior_low:
                liq_sweep_low[i] = 1

        df["liquidity_sweep_high"] = liq_sweep_high
        df["liquidity_sweep_low"] = liq_sweep_low
        # Net: positive means buy-side liquidity cleared (bearish POI)
        df["liquidity_sweep_net"] = liq_sweep_high - liq_sweep_low
        return df

    # ── 6. Impulse Strength Ratio ─────────────────────────────────────────────
    def _compute_impulse_ratio(self, df: pd.DataFrame) -> pd.DataFrame:
        """Body / full candle range — high ratio = strong impulse candle."""
        df["impulse_ratio"] = df["body_size"] / (df["candle_range"] + 1e-9)
        df["impulse_score"] = (
            df["impulse_ratio"].rolling(self.lookback).mean()
        )
        return df

    # ── 7. Structure Slope Index ──────────────────────────────────────────────
    def _compute_structure_slope(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Slope of swing highs over the lookback window.
        Positive slope = ascending structure (bullish).
        """
        shs = df["swing_high"].replace(0, np.nan).fillna(method="ffill")
        df["structure_slope"] = shs.diff(self.lookback // 2) / (self.lookback // 2)
        df["structure_slope"] = df["structure_slope"].fillna(0)
        return df

    # ── 8. Order Block Detection ──────────────────────────────────────────────
    def _compute_order_blocks(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Detect the last bearish candle before a bullish impulse (bullish OB)
        and last bullish candle before a bearish impulse (bearish OB).
        Returns distance from current close to nearest OB.
        """
        n = len(df)
        ob_bull_dist = np.zeros(n)
        ob_bear_dist = np.zeros(n)

        for i in range(5, n):
            # Check for bullish order block: bearish candle → bullish impulse
            for j in range(i - 1, max(i - 10, 0), -1):
                if df["is_bullish"].iloc[j] == 0:  # bearish candle
                    # Was there a bullish impulse after?
                    subsequent = df["impulse_ratio"].iloc[j + 1: i]
                    if not subsequent.empty and subsequent.max() > 0.6:
                        ob_level = (df["high"].iloc[j] + df["low"].iloc[j]) / 2
                        ob_bull_dist[i] = df["close"].iloc[i] - ob_level
                        break
            # Bearish OB
            for j in range(i - 1, max(i - 10, 0), -1):
                if df["is_bullish"].iloc[j] == 1:  # bullish candle
                    subsequent = df["impulse_ratio"].iloc[j + 1: i]
                    if not subsequent.empty and subsequent.max() > 0.6:
                        ob_level = (df["high"].iloc[j] + df["low"].iloc[j]) / 2
                        ob_bear_dist[i] = df["close"].iloc[i] - ob_level
                        break

        df["ob_bull_dist"] = ob_bull_dist
        df["ob_bear_dist"] = ob_bear_dist
        return df

    # ── 9. Fair Value Gap ─────────────────────────────────────────────────────
    def _compute_fvg(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        FVG: gap between candle[i-1].high and candle[i+1].low for bullish FVG.
        Price tends to revisit this gap = magnet zone.
        """
        n = len(df)
        fvg_bull = np.zeros(n)
        fvg_bear = np.zeros(n)

        for i in range(1, n - 1):
            # Bullish FVG: prev high < next low (gap on the way up)
            if df["high"].iloc[i - 1] < df["low"].iloc[i + 1]:
                fvg_bull[i] = 1
            # Bearish FVG: prev low > next high
            if df["low"].iloc[i - 1] > df["high"].iloc[i + 1]:
                fvg_bear[i] = 1

        df["fvg_bullish"] = fvg_bull
        df["fvg_bearish"] = fvg_bear
        return df
