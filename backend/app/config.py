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

    # Forextron v3 Arch weights (must sum to 1.0)
    W_PATCHTST: float = 0.35
    W_TCN: float = 0.25
    W_TFT: float = 0.30
    W_GRN: float = 0.10

    # ── Risk Rules ──────────────────────────────────────────────────────────
    RISK_PER_TRADE_PCT: float = 0.01   # 1% of balance
    MAX_DAILY_DRAWDOWN_PCT: float = 0.02  # 2% daily drawdown cap
    MAX_TRADES_PER_SESSION: int = 2
    ATR_SL_MULTIPLIER: float = 1.2
    RR_MINIMUM: float = 2.0            # Minimum risk-reward ratio

    # ── Chatbot / LLM ───────────────────────────────────────────────────────
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    HUGGINGFACE_API_KEY: str = os.getenv("HUGGINGFACE_API_KEY", "")
    HUGGINGFACE_MODEL: str = "mistralai/Mistral-7B-Instruct-v0.3"
    LLM_PROVIDER: str = "openai"             # gemini / openai / groq / huggingface
    LLM_MODEL_GEMINI: str = "gemini-2.0-flash"
    LLM_MODEL_OPENAI: str = "nvidia/nemotron-3-super-120b-a12b:free"
    LLM_MODEL_GROQ: str = "llama-3.1-70b-versatile"

    # ── MLflow ──────────────────────────────────────────────────────────────
    MLFLOW_TRACKING_URI: str = os.getenv("MLFLOW_TRACKING_URI", "mlruns")
    MLFLOW_EXPERIMENT: str = "fxguru_pro"

    # ── Finnhub ─────────────────────────────────────────────────────────────
    FINNHUB_API_KEY: str = os.getenv("FINNHUB_API_KEY", "")

    # ── Paths ────────────────────────────────────────────────────────────────
    MODEL_DIR: str = "models/saved"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
