"""
indicators.py – Technical indicator computation using pandas-ta.
Computes EMA, RSI, MACD, ATR, Bollinger Bands, rolling volatility.
All functions operate on a pandas DataFrame with OHLCV columns.
"""

import pandas as pd
import numpy as np
import pandas_ta as ta
from app.config import settings


def compute_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """
    Master indicator function. Expects columns: open, high, low, close, volume.
    Returns df with all indicator columns appended.
    """
    df = df.copy()
    df = df.sort_values("timestamp").reset_index(drop=True)

    # ── EMA ──────────────────────────────────────────────────────────────────
    df[f"ema_{settings.EMA_SHORT}"] = ta.ema(df["close"], length=settings.EMA_SHORT)
    df[f"ema_{settings.EMA_LONG}"] = ta.ema(df["close"], length=settings.EMA_LONG)
    df["ema_cross"] = (
        df[f"ema_{settings.EMA_SHORT}"] - df[f"ema_{settings.EMA_LONG}"]
    )  # positive = bullish

    # ── RSI ───────────────────────────────────────────────────────────────────
    df["rsi"] = ta.rsi(df["close"], length=settings.RSI_PERIOD)

    # ── MACD ──────────────────────────────────────────────────────────────────
    macd = ta.macd(df["close"],
                   fast=settings.MACD_FAST,
                   slow=settings.MACD_SLOW,
                   signal=settings.MACD_SIGNAL)
    if macd is not None and not macd.empty:
        df["macd"] = macd.iloc[:, 0]
        df["macd_signal"] = macd.iloc[:, 2]
        df["macd_hist"] = macd.iloc[:, 1]
    else:
        df["macd"] = df["macd_signal"] = df["macd_hist"] = 0.0

    # ── ATR ───────────────────────────────────────────────────────────────────
    df["atr"] = ta.atr(df["high"], df["low"], df["close"], length=settings.ATR_PERIOD)

    # ── Bollinger Bands ───────────────────────────────────────────────────────
    bb = ta.bbands(df["close"], length=settings.BB_PERIOD, std=settings.BB_STD)
    if bb is not None and not bb.empty:
        df["bb_upper"] = bb.iloc[:, 0]
        df["bb_mid"] = bb.iloc[:, 1]
        df["bb_lower"] = bb.iloc[:, 2]
        df["bb_width"] = bb.iloc[:, 3]
        df["bb_pct"] = bb.iloc[:, 4]
    else:
        df["bb_upper"] = df["bb_mid"] = df["bb_lower"] = df["close"]
        df["bb_width"] = df["bb_pct"] = 0.0

    # ── Stochastic RSI (extra signal) ─────────────────────────────────────────
    stoch = ta.stochrsi(df["close"], length=14, rsi_length=14, k=3, d=3)
    if stoch is not None and not stoch.empty:
        df["stoch_k"] = stoch.iloc[:, 0]
        df["stoch_d"] = stoch.iloc[:, 1]
    else:
        df["stoch_k"] = df["stoch_d"] = 50.0

    # ── Williams %R ───────────────────────────────────────────────────────────
    df["willr"] = ta.willr(df["high"], df["low"], df["close"], length=14)

    # ── CCI ───────────────────────────────────────────────────────────────────
    df["cci"] = ta.cci(df["high"], df["low"], df["close"], length=20)

    # ── Rolling Volatility ────────────────────────────────────────────────────
    df["rolling_vol_10"] = df["close"].pct_change().rolling(10).std() * np.sqrt(252 * 288)
    df["rolling_vol_20"] = df["close"].pct_change().rolling(20).std() * np.sqrt(252 * 288)

    # ── Candle Properties ─────────────────────────────────────────────────────
    df["body_size"] = abs(df["close"] - df["open"])
    df["candle_range"] = df["high"] - df["low"]
    df["upper_wick"] = df["high"] - df[["open", "close"]].max(axis=1)
    df["lower_wick"] = df[["open", "close"]].min(axis=1) - df["low"]
    df["body_ratio"] = df["body_size"] / (df["candle_range"] + 1e-9)
    df["is_bullish"] = (df["close"] > df["open"]).astype(int)

    # ── Trend strength (ADX) ──────────────────────────────────────────────────
    adx = ta.adx(df["high"], df["low"], df["close"], length=14)
    if adx is not None and not adx.empty:
        df["adx"] = adx.iloc[:, 0]
        df["dmp"] = adx.iloc[:, 1]
        df["dmn"] = adx.iloc[:, 2]
    else:
        df["adx"] = df["dmp"] = df["dmn"] = 25.0

    df = df.fillna(0)
    return df
