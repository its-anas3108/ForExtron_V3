"""
config.py – Central configuration for ForEX Pro
All environment variables are loaded from .env
"""

import os
from dotenv import load_dotenv
from pydantic_settings import BaseSettings
from typing import List

load_dotenv()


class Settings(BaseSettings):
    # ── OANDA ──────────────────────────────────────────────────────────────
    OANDA_API_KEY: str = os.getenv("OANDA_API_KEY", "YOUR_OANDA_API_KEY")
    OANDA_ACCOUNT_ID: str = os.getenv("OANDA_ACCOUNT_ID", "YOUR_ACCOUNT_ID")
    # Practice: https://api-fxpractice.oanda.com
    # Live:     https://api-fxtrade.oanda.com
    OANDA_BASE_URL: str = os.getenv(
        "OANDA_BASE_URL", "https://api-fxpractice.oanda.com"
    )
    OANDA_STREAM_URL: str = os.getenv(
        "OANDA_STREAM_URL", "https://stream-fxpractice.oanda.com"
    )

    # ── MongoDB ─────────────────────────────────────────────────────────────
    MONGO_URI: str = os.getenv("MONGO_URI", "mongodb://localhost:27017")
    MONGO_DB_NAME: str = os.getenv("MONGO_DB_NAME", "fxguru_pro")

    # ── Supported Instruments (including INR pairs) ─────────────────────────
    INSTRUMENTS: List[str] = [
        "EUR_USD",
        "GBP_USD",
        "USD_JPY",
        "AUD_USD",
        "USD_CHF",
        "USD_CAD",
        "NZD_USD",
        "USD_INR",  # Indian Rupee pairs
        "EUR_INR",
        "GBP_INR",
    ]
    DEFAULT_INSTRUMENT: str = "EUR_USD"
    DEFAULT_TIMEFRAME: str = "M5"  # 5-minute candles

    # ── Feature Engineering ─────────────────────────────────────────────────
    EMA_SHORT: int = 10
    EMA_LONG: int = 50
    RSI_PERIOD: int = 14
    ATR_PERIOD: int = 14
    MACD_FAST: int = 12
    MACD_SLOW: int = 26
    MACD_SIGNAL: int = 9
    BB_PERIOD: int = 20
    BB_STD: float = 2.0
    LOOKBACK_CANDLES: int = 50       # sequence length for GRU/CNN
    STRUCTURE_LOOKBACK: int = 20     # swing detection window

    # ── ML / Model Thresholds ───────────────────────────────────────────────
    BUY_THRESHOLD_DEFAULT: float = 0.70
    BUY_THRESHOLD_MIN: float = 0.65
    BUY_THRESHOLD_MAX: float = 0.75
    DRIFT_DROP_THRESHOLD: float = 0.15  # 15% confidence drop triggers retrain
    HOLD_RATIO_THRESHOLD: float = 0.60  # >60% hold signals triggers retrain

    # Ensemble weights  (must sum to 1.0)
    W_LOGISTIC: float = 0.10
    W_DNN: float = 0.20
    W_GRU: float = 0.30
    W_CNN: float = 0.25
    W_TRANSFORMER: float = 0.15

    # ── Risk Rules ──────────────────────────────────────────────────────────
    RISK_PER_TRADE_PCT: float = 0.01   # 1% of balance
    MAX_DAILY_DRAWDOWN_PCT: float = 0.02  # 2% daily drawdown cap
    MAX_TRADES_PER_SESSION: int = 2
    ATR_SL_MULTIPLIER: float = 1.2
    RR_MINIMUM: float = 2.0            # Minimum risk-reward ratio

    # ── Chatbot / LLM ───────────────────────────────────────────────────────
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "gemini")  # "gemini" | "openai"
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "YOUR_GEMINI_API_KEY")
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    LLM_MODEL_GEMINI: str = "gemini-2.0-flash"
    LLM_MODEL_OPENAI: str = "gpt-4o-mini"

    # ── MLflow ──────────────────────────────────────────────────────────────
    MLFLOW_TRACKING_URI: str = os.getenv("MLFLOW_TRACKING_URI", "mlruns")
    MLFLOW_EXPERIMENT: str = "fxguru_pro"

    # ── Paths ────────────────────────────────────────────────────────────────
    MODEL_DIR: str = "models/saved"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
