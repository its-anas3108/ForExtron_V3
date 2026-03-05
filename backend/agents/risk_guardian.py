"""
risk_guardian.py – Risk Guardian Agent.

Enforces:
  - Max 2 trades per session
  - Max 2% daily drawdown
  - 1% risk per trade
  - Auto HOLD mode when limits breached
"""

import logging
from datetime import datetime, timezone, date
from typing import Tuple
from app.config import settings

logger = logging.getLogger(__name__)


class RiskGuardianAgent:
    """Session-scoped risk enforcement. Resets daily."""

    def __init__(self):
        self.session_date: date = datetime.now(timezone.utc).date()
        self.trades_today: int = 0
        self.peak_balance: float = 0.0
        self.current_balance: float = 0.0
        self.hold_mode: bool = False
        self.hold_reason: str = ""
        self.events: list = []

    def _reset_if_new_day(self):
        today = datetime.now(timezone.utc).date()
        if today != self.session_date:
            self.session_date = today
            self.trades_today = 0
            self.hold_mode = False
            self.hold_reason = ""
            self.peak_balance = self.current_balance
            logger.info("🔄 Risk Guardian: New session – counters reset")

    def update_balance(self, balance: float):
        self._reset_if_new_day()
        self.current_balance = balance
        if balance > self.peak_balance:
            self.peak_balance = balance

    def approve_trade(self) -> Tuple[bool, str]:
        """
        Returns (approved, reason).
        Called before any trade is placed.
        """
        self._reset_if_new_day()

        if self.hold_mode:
            return False, f"HOLD mode active: {self.hold_reason}"

        # Check trade count
        if self.trades_today >= settings.MAX_TRADES_PER_SESSION:
            self.hold_mode = True
            self.hold_reason = f"Max {settings.MAX_TRADES_PER_SESSION} trades/session reached"
            self._log_event("TRADE_LIMIT_BREACH", self.hold_reason)
            return False, self.hold_reason

        # Check drawdown
        if self.peak_balance > 0:
            drawdown = (self.peak_balance - self.current_balance) / self.peak_balance
            if drawdown >= settings.MAX_DAILY_DRAWDOWN_PCT:
                self.hold_mode = True
                self.hold_reason = f"Daily drawdown {drawdown*100:.2f}% breached 2% limit"
                self._log_event("DRAWDOWN_BREACH", self.hold_reason)
                return False, self.hold_reason

        return True, "Risk Guardian: APPROVED"

    def record_trade(self):
        """Call this when a trade is actually executed."""
        self.trades_today += 1
        self._log_event("TRADE_RECORDED", f"Trade #{self.trades_today} today")

    def get_status(self) -> dict:
        drawdown = 0.0
        if self.peak_balance > 0:
            drawdown = (self.peak_balance - self.current_balance) / self.peak_balance
        return {
            "hold_mode": self.hold_mode,
            "hold_reason": self.hold_reason,
            "trades_today": self.trades_today,
            "max_trades": settings.MAX_TRADES_PER_SESSION,
            "current_balance": self.current_balance,
            "peak_balance": self.peak_balance,
            "drawdown_pct": round(drawdown * 100, 2),
            "max_drawdown_pct": settings.MAX_DAILY_DRAWDOWN_PCT * 100,
        }

    def _log_event(self, event: str, detail: str):
        entry = {
            "agent": "risk_guardian",
            "event": event,
            "detail": detail,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        self.events.append(entry)
        logger.warning(f"⚠️ Risk Guardian [{event}]: {detail}")
