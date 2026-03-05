"""
logistic_model.py – Logistic Regression baseline for ensemble stability.
"""

import numpy as np
import joblib
import os
import logging
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from app.config import settings

logger = logging.getLogger(__name__)
MODEL_PATH = os.path.join(settings.MODEL_DIR, "logistic_model.pkl")


class LogisticModel:
    def __init__(self):
        self.pipeline = Pipeline([
            ("scaler", StandardScaler()),
            ("model", LogisticRegression(max_iter=1000, C=0.5, solver="lbfgs")),
        ])
        self._load()

    def _load(self):
        if os.path.exists(MODEL_PATH):
            self.pipeline = joblib.load(MODEL_PATH)
            logger.info("✅ Logistic model loaded from disk")

    def train(self, X: np.ndarray, y: np.ndarray):
        self.pipeline.fit(X, y)
        self.save()

    def predict_proba(self, X: np.ndarray) -> float:
        try:
            proba = self.pipeline.predict_proba(X)
            return float(proba[0][1])  # probability of class 1 (bullish)
        except Exception:
            return 0.5

    def save(self):
        os.makedirs(settings.MODEL_DIR, exist_ok=True)
        joblib.dump(self.pipeline, MODEL_PATH)
