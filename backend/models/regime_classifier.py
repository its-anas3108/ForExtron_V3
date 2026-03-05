"""
regime_classifier.py – XGBoost-based Volatility Regime Classifier.
Classifies market state as: Accumulation / Expansion / Exhaustion / Anomaly.
"""

import numpy as np
import pandas as pd
import joblib
import os
import logging
from typing import Tuple, Optional

from xgboost import XGBClassifier
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
from app.config import settings

logger = logging.getLogger(__name__)

REGIME_FEATURES = [
    "atr_percentile", "atr_z", "bb_width_percentile", "bb_width_z",
    "vol_z", "vol_of_vol", "hl_ratio_ma", "momentum_5", "momentum_10",
    "momentum_20", "hurst", "candle_size_z", "rolling_std_10", "rolling_std_20",
    "adx", "rsi", "rolling_vol_10",
]

MODEL_PATH = os.path.join(settings.MODEL_DIR, "regime_classifier.pkl")
ENCODER_PATH = os.path.join(settings.MODEL_DIR, "regime_encoder.pkl")


class RegimeClassifier:

    def __init__(self):
        self.model: Optional[XGBClassifier] = None
        self.encoder = LabelEncoder()
        self._load_or_init()

    def _load_or_init(self):
        if os.path.exists(MODEL_PATH):
            self.model = joblib.load(MODEL_PATH)
            self.encoder = joblib.load(ENCODER_PATH)
            logger.info("✅ Regime classifier loaded from disk")
        else:
            self.model = XGBClassifier(
                n_estimators=300,
                max_depth=6,
                learning_rate=0.05,
                subsample=0.8,
                colsample_bytree=0.8,
                use_label_encoder=False,
                eval_metric="mlogloss",
                random_state=42,
                n_jobs=-1,
            )
            logger.info("⚙️ Regime classifier initialized (not trained)")

    def train(self, df: pd.DataFrame, label_col: str = "regime_label") -> dict:
        """Train on labeled historical data."""
        available = [f for f in REGIME_FEATURES if f in df.columns]
        X = df[available].fillna(0).values
        y = df[label_col].values
        y_enc = self.encoder.fit_transform(y)

        X_train, X_val, y_train, y_val = train_test_split(X, y_enc, test_size=0.2, random_state=42)
        self.model.fit(
            X_train, y_train,
            eval_set=[(X_val, y_val)],
            early_stopping_rounds=30,
            verbose=False,
        )

        preds = self.model.predict(X_val)
        report = classification_report(y_val, preds, output_dict=True)
        self.save()
        logger.info(f"Regime classifier trained. Val accuracy: {report['accuracy']:.3f}")
        return report

    def predict(self, df: pd.DataFrame) -> Tuple[str, float]:
        """Predict regime for the latest candle row."""
        if self.model is None:
            return "accumulation", 0.5

        available = [f for f in REGIME_FEATURES if f in df.columns]
        row = df[available].fillna(0).iloc[[-1]].values

        try:
            proba = self.model.predict_proba(row)[0]
            idx = int(np.argmax(proba))
            regime = self.encoder.inverse_transform([idx])[0]
            confidence = float(proba[idx])
            return regime, confidence
        except Exception as e:
            logger.warning(f"Regime prediction error: {e}")
            return "accumulation", 0.5

    def save(self):
        os.makedirs(settings.MODEL_DIR, exist_ok=True)
        joblib.dump(self.model, MODEL_PATH)
        joblib.dump(self.encoder, ENCODER_PATH)
        logger.info("Regime classifier saved.")

    def get_feature_importance(self) -> dict:
        if self.model and hasattr(self.model, "feature_importances_"):
            available = [f for f in REGIME_FEATURES]
            fi = dict(zip(available, self.model.feature_importances_))
            return dict(sorted(fi.items(), key=lambda x: x[1], reverse=True))
        return {}
