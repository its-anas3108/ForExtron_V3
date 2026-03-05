"""
regime_features.py – Volatility regime feature computation.
Provides features for the XGBoost/RandomForest regime classifier.
"""

import pandas as pd
import numpy as np
from scipy import stats


def compute_regime_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Computes volatility regime features:
    - ATR percentile rank
    - BB width percentile rank
    - Rolling std z-score
    - Volatility clustering (rolling std of std)
    - Price momentum features
    - Regime label (for training) – only present in labeled data
    """
    df = df.copy()

    # ── ATR Percentile ────────────────────────────────────────────────────────
    if "atr" in df.columns:
        df["atr_percentile"] = df["atr"].rank(pct=True)
        df["atr_z"] = (df["atr"] - df["atr"].rolling(50).mean()) / (df["atr"].rolling(50).std() + 1e-9)
    else:
        df["atr_percentile"] = 0.5
        df["atr_z"] = 0.0

    # ── BB Width Percentile ───────────────────────────────────────────────────
    if "bb_width" in df.columns:
        df["bb_width_percentile"] = df["bb_width"].rank(pct=True)
        df["bb_width_z"] = (
            (df["bb_width"] - df["bb_width"].rolling(50).mean())
            / (df["bb_width"].rolling(50).std() + 1e-9)
        )
    else:
        df["bb_width_percentile"] = 0.5
        df["bb_width_z"] = 0.0

    # ── Rolling Std Z-Score ───────────────────────────────────────────────────
    df["returns"] = df["close"].pct_change()
    df["rolling_std_10"] = df["returns"].rolling(10).std()
    df["rolling_std_20"] = df["returns"].rolling(20).std()
    df["vol_z"] = (
        (df["rolling_std_10"] - df["rolling_std_20"])
        / (df["rolling_std_20"] + 1e-9)
    )

    # ── Volatility-of-Volatility (Clustering) ─────────────────────────────────
    df["vol_of_vol"] = df["rolling_std_10"].rolling(10).std()

    # ── High-Low Expansion Ratio ──────────────────────────────────────────────
    df["hl_ratio"] = (df["high"] - df["low"]) / (df["close"].shift(1).abs() + 1e-9)
    df["hl_ratio_ma"] = df["hl_ratio"].rolling(10).mean()

    # ── Price Momentum ────────────────────────────────────────────────────────
    df["momentum_5"] = df["close"].pct_change(5)
    df["momentum_10"] = df["close"].pct_change(10)
    df["momentum_20"] = df["close"].pct_change(20)

    # ── Hurst Exponent (trend persistence) — rolling estimate ─────────────────
    df["hurst"] = _rolling_hurst(df["close"], window=30)

    # ── News Anomaly Spike Detection ─────────────────────────────────────────
    df["candle_size_z"] = (
        (df["candle_range"] - df["candle_range"].rolling(20).mean())
        / (df["candle_range"].rolling(20).std() + 1e-9)
    )
    df["is_anomaly"] = (df["candle_size_z"].abs() > 3).astype(int)

    df = df.fillna(0)
    return df


def _rolling_hurst(series: pd.Series, window: int = 30) -> pd.Series:
    """
    Approximate rolling Hurst exponent using R/S analysis.
    H > 0.5 = trending, H < 0.5 = mean-reverting, H ≈ 0.5 = random walk.
    """
    n = len(series)
    hurst_vals = np.zeros(n)

    for i in range(window, n):
        chunk = series.iloc[i - window: i].values
        try:
            log_returns = np.diff(np.log(chunk + 1e-9))
            lags = range(2, min(20, window // 2))
            rs_values = []
            for lag in lags:
                sub = log_returns[:lag]
                mean = np.mean(sub)
                dev = np.cumsum(sub - mean)
                r = max(dev) - min(dev)
                s = np.std(sub) + 1e-9
                rs_values.append(r / s)
            if len(rs_values) > 1:
                slope, _, _, _, _ = stats.linregress(np.log(list(lags)), np.log(rs_values))
                hurst_vals[i] = np.clip(slope, 0.0, 1.0)
            else:
                hurst_vals[i] = 0.5
        except Exception:
            hurst_vals[i] = 0.5

    return pd.Series(hurst_vals, index=series.index)


# ── Regime label mapping for training ─────────────────────────────────────────
REGIME_LABELS = {
    0: "accumulation",
    1: "expansion",
    2: "exhaustion",
    3: "anomaly",
}

REGIME_COLORS = {
    "accumulation": "#F59E0B",
    "expansion": "#10B981",
    "exhaustion": "#EF4444",
    "anomaly": "#8B5CF6",
}
