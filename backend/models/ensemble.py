"""
ensemble.py – Meta Fusion Ensemble Layer.
Combines predictions from Logistic, DNN, GRU, CNN, and Transformer models.

Weights:
  Logistic Regression : 0.10
  DNN                 : 0.20
  GRU                 : 0.30
  CNN                 : 0.25
  Transformer         : 0.15
"""

import numpy as np
import pandas as pd
import torch
import logging
from typing import Tuple, Dict

from models.logistic_model import LogisticModel
from models.dnn_model import DNNModel
from models.gru_model import GRUModel
from models.cnn_model import CNNModel
from models.transformer_model import TransformerModel
from app.config import settings

logger = logging.getLogger(__name__)

# All structured feature columns used by non-sequential models
FEATURE_COLS = [
    "ema_10", "ema_50", "ema_cross", "rsi", "macd", "macd_hist",
    "atr", "bb_width", "bb_pct", "adx", "dmp", "dmn",
    "body_ratio", "impulse_ratio", "impulse_score", "is_bullish",
    "bos_bullish", "bos_bearish", "bos_net", "choch",
    "liquidity_sweep_high", "liquidity_sweep_low", "liquidity_sweep_net",
    "hh_ll_score", "trend_bias", "structure_slope",
    "ob_bull_dist", "ob_bear_dist", "fvg_bullish", "fvg_bearish",
    "atr_percentile", "atr_z", "bb_width_percentile", "vol_z",
    "hurst", "momentum_5", "momentum_10", "stoch_k", "stoch_d",
    "willr", "cci", "candle_size_z",
]


class EnsembleModel:
    """Weighted ensemble of 5 models producing a final directional probability."""

    def __init__(self):
        self.logistic = LogisticModel()
        self.dnn = DNNModel(input_dim=len(FEATURE_COLS))
        self.gru = GRUModel(input_dim=len(FEATURE_COLS))
        self.cnn = CNNModel(input_dim=len(FEATURE_COLS))
        self.transformer = TransformerModel(input_dim=len(FEATURE_COLS))

        self.weights = {
            "logistic": settings.W_LOGISTIC,
            "dnn": settings.W_DNN,
            "gru": settings.W_GRU,
            "cnn": settings.W_CNN,
            "transformer": settings.W_TRANSFORMER,
        }

    def predict(self, df: pd.DataFrame) -> Tuple[float, Dict[str, float]]:
        """
        Returns:
            final_prob: float [0,1] — probability of bullish direction
            individual: dict of each model's probability
        """
        available_cols = [c for c in FEATURE_COLS if c in df.columns]
        feature_vector = df[available_cols].fillna(0).iloc[-1].values.astype(np.float32)
        sequence = self._get_sequence(df, available_cols)

        individual = {}

        # 1. Logistic Regression
        try:
            p_logistic = self.logistic.predict_proba(feature_vector.reshape(1, -1))
            individual["logistic"] = float(p_logistic)
        except Exception as e:
            logger.warning(f"Logistic predict error: {e}")
            individual["logistic"] = 0.5

        # 2. DNN
        try:
            p_dnn = self.dnn.predict(feature_vector)
            individual["dnn"] = float(p_dnn)
        except Exception as e:
            logger.warning(f"DNN predict error: {e}")
            individual["dnn"] = 0.5

        # 3. GRU (sequence model)
        try:
            p_gru = self.gru.predict(sequence)
            individual["gru"] = float(p_gru)
        except Exception as e:
            logger.warning(f"GRU predict error: {e}")
            individual["gru"] = 0.5

        # 4. CNN (sequence model)
        try:
            p_cnn = self.cnn.predict(sequence)
            individual["cnn"] = float(p_cnn)
        except Exception as e:
            logger.warning(f"CNN predict error: {e}")
            individual["cnn"] = 0.5

        # 5. Transformer (sequence model)
        try:
            p_transformer = self.transformer.predict(sequence)
            individual["transformer"] = float(p_transformer)
        except Exception as e:
            logger.warning(f"Transformer predict error: {e}")
            individual["transformer"] = 0.5

        # ── Weighted Fusion ────────────────────────────────────────────────
        final_prob = sum(
            self.weights[name] * prob for name, prob in individual.items()
        )
        final_prob = float(np.clip(final_prob, 0.0, 1.0))

        logger.debug(
            f"Ensemble → Final: {final_prob:.3f} | "
            + " | ".join(f"{k}: {v:.3f}" for k, v in individual.items())
        )

        return final_prob, individual

    def _get_sequence(self, df: pd.DataFrame, cols: list) -> np.ndarray:
        """Extract the last LOOKBACK_CANDLES rows as a 3D sequence."""
        lookback = settings.LOOKBACK_CANDLES
        data = df[cols].fillna(0).values.astype(np.float32)
        if len(data) >= lookback:
            seq = data[-lookback:]
        else:
            # Pad with zeros at the front
            pad = np.zeros((lookback - len(data), len(cols)), dtype=np.float32)
            seq = np.vstack([pad, data])
        return seq  # shape: (lookback, n_features)
