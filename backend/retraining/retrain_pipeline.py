"""
retrain_pipeline.py – Automated model retraining triggered by Drift Agent.
Fetches recent candles, builds features, retrains DNN + GRU + CNN + Transformer.
"""

import logging
import pandas as pd
import numpy as np
import asyncio
from datetime import datetime, timezone

from app.config import settings
from features.indicators import compute_indicators
from features.structure_engine import StructureEngine
from features.regime_features import compute_regime_features
from models.dnn_model import DNNModel
from models.gru_model import GRUModel
from models.cnn_model import CNNModel
from models.transformer_model import TransformerModel
from models.ensemble import FEATURE_COLS

logger = logging.getLogger(__name__)
structure_engine = StructureEngine()


class RetrainPipeline:

    def run(self, instrument: str = None) -> dict:
        """Synchronous retrain method (run via executor)."""
        instruments = [instrument] if instrument else settings.INSTRUMENTS[:3]
        try:
            logger.info("🔁 Retrain pipeline starting...")
            all_dfs = []

            # Fetch data for each instrument
            from data.oanda_client import oanda
            for pair in instruments:
                try:
                    candles = oanda.get_historical_candles(pair, count=1000)
                    if not candles:
                        continue
                    df = pd.DataFrame(candles)
                    df = compute_indicators(df)
                    df = compute_regime_features(df)
                    df = structure_engine.compute(df)
                    df["pair"] = pair
                    all_dfs.append(df)
                except Exception as e:
                    logger.warning(f"Retrain: failed to fetch {pair}: {e}")

            if not all_dfs:
                return {"success": False, "error": "No data fetched"}

            combined = pd.concat(all_dfs, ignore_index=True)
            combined = combined.dropna()

            # Create directional label (1=up, 0=down over next candle)
            combined["future_close"] = combined["close"].shift(-1)
            combined["label"] = (combined["future_close"] > combined["close"]).astype(int)
            combined = combined.dropna()

            if len(combined) < 100:
                return {"success": False, "error": "Insufficient training data"}

            available_cols = [c for c in FEATURE_COLS if c in combined.columns]
            X = combined[available_cols].fillna(0).values.astype(np.float32)
            y = combined["label"].values.astype(np.float32)

            # Build sequences for GRU/CNN/Transformer
            X_seq = self._build_sequences(X, y, settings.LOOKBACK_CANDLES)
            y_seq = X_seq[1]
            X_seq = X_seq[0]

            # Retrain all DL models
            input_dim = X.shape[1]
            dnn = DNNModel(input_dim=input_dim)
            dnn.train_model(X, y, epochs=30)

            gru = GRUModel(input_dim=input_dim)
            gru.train_model(X_seq, y_seq, epochs=20)

            cnn = CNNModel(input_dim=input_dim)
            cnn.train_model(X_seq, y_seq, epochs=20)

            transformer = TransformerModel(input_dim=input_dim)
            transformer.train_model(X_seq, y_seq, epochs=20)

            logger.info("✅ Retrain complete for all models")
            return {
                "success": True,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "samples": len(combined),
                "instruments": instruments,
            }

        except Exception as e:
            logger.error(f"Retrain pipeline error: {e}", exc_info=True)
            return {"success": False, "error": str(e)}

    def _build_sequences(self, X: np.ndarray, y: np.ndarray, seq_len: int):
        """Build (N, seq_len, features) sequences from flat array."""
        sequences, labels = [], []
        for i in range(seq_len, len(X)):
            sequences.append(X[i - seq_len: i])
            labels.append(y[i])
        return np.array(sequences), np.array(labels)
