"""
models.py – Pydantic v2 models for all MongoDB collections.
"""

from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field


class Candle(BaseModel):
    pair: str
    timeframe: str
    timestamp: str
    open: float
    high: float
    low: float
    close: float
    volume: int


class Signal(BaseModel):
    pair: str
    timestamp: str
    regime: str
    regime_confidence: float
    structure_bias: str
    liquidity_sweep_below: bool
    ensemble_probability: float
    model_contributions: Dict[str, float] = {}
    decision: str                          # BUY / SELL / HOLD
    threshold_used: float
    sl: Optional[float] = None
    tp: Optional[float] = None
    lot_size: Optional[float] = None
    rr: float = 0.0
    atr: float = 0.0
    rsi: float = 50.0
    gate_log: Dict[str, Any] = {}
    agent_approval: bool = False


class Trade(BaseModel):
    user_email: str
    pair: str
    entry_price: float
    exit_price: Optional[float] = None
    sl: float
    tp: float
    lot_size: float
    direction: str                         # BUY / SELL
    result: Optional[str] = None          # WIN / LOSS / OPEN
    pnl: Optional[float] = None
    rr_achieved: Optional[float] = None
    entry_time: str
    exit_time: Optional[str] = None
    oanda_trade_id: Optional[str] = None


class AgentLog(BaseModel):
    agent_name: str
    event: str
    detail: str
    timestamp: str


class PerformanceMetrics(BaseModel):
    pair: str
    period: str                            # e.g. "daily", "weekly"
    win_rate: float
    total_trades: int
    winning_trades: int
    losing_trades: int
    max_drawdown_pct: float
    expectancy: float
    sharpe_ratio: float
    profit_factor: float
    avg_rr: float
    timestamp: str


class ChatMessage(BaseModel):
    session_id: str
    role: str                              # "user" / "assistant"
    message: str
    intent: Optional[str] = None
    context_data: Dict[str, Any] = {}
    timestamp: str


class ChatRequest(BaseModel):
    message: str
    session_id: str = "default"
    instrument: str = "EUR_USD"

# ── User Authentication & Account Models ────────────────────────────────────

from pydantic import EmailStr

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    name: str

class UserResponse(BaseModel):
    id: str = Field(alias="_id")
    email: EmailStr
    name: str
    balance: float
    created_at: str

class UserInDB(BaseModel):
    email: str
    hashed_password: str
    name: str
    balance: float = 10000.0  # Default demo starting balance
    created_at: str = Field(default_factory=lambda: datetime.now().astimezone().isoformat())

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

class AccountSummaryResponse(BaseModel):
    balance: float
    equity: float
    total_pnl: float
    win_rate: float
    total_trades: int
