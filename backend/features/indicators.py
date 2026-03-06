"""
indicators.py – Technical indicator computation.
Computes EMA, RSI, MACD, ATR, Bollinger Bands, rolling volatility.
All functions operate on a pandas DataFrame with OHLCV columns.
Pure pandas/numpy fallback (no pandas-ta dependency).
"""

import pandas as pd
import numpy as np
from app.config import settings


# ── Pure pandas/numpy indicator helpers ──────────────────────────────────────

def _ema(series: pd.Series, length: int) -> pd.Series:
    return series.ewm(span=length, adjust=False).mean()


def _rsi(series: pd.Series, length: int = 14) -> pd.Series:
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(alpha=1 / length, min_periods=length, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1 / length, min_periods=length, adjust=False).mean()
    rs = avg_gain / (avg_loss + 1e-9)
    return 100 - (100 / (1 + rs))


def _macd(series: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9):
    ema_fast = _ema(series, fast)
    ema_slow = _ema(series, slow)
    macd_line = ema_fast - ema_slow
    signal_line = _ema(macd_line, signal)
    hist = macd_line - signal_line
    return macd_line, signal_line, hist


def _atr(high: pd.Series, low: pd.Series, close: pd.Series, length: int = 14) -> pd.Series:
    prev_close = close.shift(1)
    tr = pd.concat([
        high - low,
        (high - prev_close).abs(),
        (low - prev_close).abs()
    ], axis=1).max(axis=1)
    return tr.ewm(span=length, adjust=False).mean()


def _bbands(series: pd.Series, length: int = 20, std: float = 2.0):
    mid = series.rolling(window=length).mean()
    rolling_std = series.rolling(window=length).std()
    upper = mid + std * rolling_std
    lower = mid - std * rolling_std
    width = (upper - lower) / (mid + 1e-9)
    pct = (series - lower) / (upper - lower + 1e-9)
    return upper, mid, lower, width, pct


def _stochrsi(series: pd.Series, length: int = 14, rsi_length: int = 14, k: int = 3, d: int = 3):
    rsi = _rsi(series, rsi_length)
    rsi_min = rsi.rolling(window=length).min()
    rsi_max = rsi.rolling(window=length).max()
    stoch_rsi = (rsi - rsi_min) / (rsi_max - rsi_min + 1e-9) * 100
    stoch_k = stoch_rsi.rolling(window=k).mean()
    stoch_d = stoch_k.rolling(window=d).mean()
    return stoch_k, stoch_d


def _willr(high: pd.Series, low: pd.Series, close: pd.Series, length: int = 14) -> pd.Series:
    highest = high.rolling(window=length).max()
    lowest = low.rolling(window=length).min()
    return -100 * (highest - close) / (highest - lowest + 1e-9)


def _cci(high: pd.Series, low: pd.Series, close: pd.Series, length: int = 20) -> pd.Series:
    tp = (high + low + close) / 3
    sma = tp.rolling(window=length).mean()
    mad = tp.rolling(window=length).apply(lambda x: np.abs(x - x.mean()).mean(), raw=True)
    return (tp - sma) / (0.015 * mad + 1e-9)


def _adx(high: pd.Series, low: pd.Series, close: pd.Series, length: int = 14):
    prev_high = high.shift(1)
    prev_low = low.shift(1)
    plus_dm = (high - prev_high).clip(lower=0)
    minus_dm = (prev_low - low).clip(lower=0)
    plus_dm[plus_dm < minus_dm] = 0
    minus_dm[minus_dm < plus_dm] = 0
    atr = _atr(high, low, close, length)
    plus_di = 100 * _ema(plus_dm, length) / (atr + 1e-9)
    minus_di = 100 * _ema(minus_dm, length) / (atr + 1e-9)
    dx = 100 * (plus_di - minus_di).abs() / (plus_di + minus_di + 1e-9)
    adx_val = _ema(dx, length)
    return adx_val, plus_di, minus_di


# ── Master indicator function ────────────────────────────────────────────────

def compute_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """
    Master indicator function. Expects columns: open, high, low, close, volume.
    Returns df with all indicator columns appended.
    """
    df = df.copy()
    df = df.sort_values("timestamp").reset_index(drop=True)

    # ── EMA ──────────────────────────────────────────────────────────────────
    df[f"ema_{settings.EMA_SHORT}"] = _ema(df["close"], length=settings.EMA_SHORT)
    df[f"ema_{settings.EMA_LONG}"] = _ema(df["close"], length=settings.EMA_LONG)
    df["ema_cross"] = (
        df[f"ema_{settings.EMA_SHORT}"] - df[f"ema_{settings.EMA_LONG}"]
    )  # positive = bullish

    # ── RSI ───────────────────────────────────────────────────────────────────
    df["rsi"] = _rsi(df["close"], length=settings.RSI_PERIOD)

    # ── MACD ──────────────────────────────────────────────────────────────────
    macd_line, macd_signal, macd_hist = _macd(
        df["close"],
        fast=settings.MACD_FAST,
        slow=settings.MACD_SLOW,
        signal=settings.MACD_SIGNAL,
    )
    df["macd"] = macd_line
    df["macd_signal"] = macd_signal
    df["macd_hist"] = macd_hist

    # ── ATR ───────────────────────────────────────────────────────────────────
    df["atr"] = _atr(df["high"], df["low"], df["close"], length=settings.ATR_PERIOD)

    # ── Bollinger Bands ───────────────────────────────────────────────────────
    bb_upper, bb_mid, bb_lower, bb_width, bb_pct = _bbands(
        df["close"], length=settings.BB_PERIOD, std=settings.BB_STD
    )
    df["bb_upper"] = bb_upper
    df["bb_mid"] = bb_mid
    df["bb_lower"] = bb_lower
    df["bb_width"] = bb_width
    df["bb_pct"] = bb_pct

    # ── Stochastic RSI (extra signal) ─────────────────────────────────────────
    stoch_k, stoch_d = _stochrsi(df["close"], length=14, rsi_length=14, k=3, d=3)
    df["stoch_k"] = stoch_k
    df["stoch_d"] = stoch_d

    # ── Williams %R ───────────────────────────────────────────────────────────
    df["willr"] = _willr(df["high"], df["low"], df["close"], length=14)

    # ── CCI ───────────────────────────────────────────────────────────────────
    df["cci"] = _cci(df["high"], df["low"], df["close"], length=20)

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
    adx_val, dmp, dmn = _adx(df["high"], df["low"], df["close"], length=14)
    df["adx"] = adx_val
    df["dmp"] = dmp
    df["dmn"] = dmn

    df = df.fillna(0)
    return df
