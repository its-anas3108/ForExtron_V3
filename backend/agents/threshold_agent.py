"""
threshold_agent.py – Dynamic threshold optimization agent.
Adjusts buy probability threshold based on regime performance history.
"""

import logging
from collections import defaultdict, deque
from app.config import settings

logger = logging.getLogger(__name__)


class ThresholdAgent:
    """
    Tracks win rate per regime and adjusts threshold accordingly.
    Higher confidence required in uncertain regimes.
    """

    def __init__(self):
        # regime → deque of (was_correct: bool)
        self.regime_outcomes: defaultdict = defaultdict(lambda: deque(maxlen=50))
        self.current_threshold: float = settings.BUY_THRESHOLD_DEFAULT
        self.events: list = []

    def record_outcome(self, regime: str, was_correct: bool):
        self.regime_outcomes[regime].append(was_correct)
        self._recalibrate()

    def get_threshold(self, regime: str) -> float:
        """Return dynamically adjusted threshold for the given regime."""
        self._recalibrate()
        return self.current_threshold

    def _recalibrate(self):
        """Raise threshold in weak regimes, lower slightly in strong ones."""
        if not any(len(v) >= 10 for v in self.regime_outcomes.values()):
            return  # Not enough data

        overall_corrections = []
        for outcomes in self.regime_outcomes.values():
            if len(outcomes) >= 10:
                overall_corrections.extend(list(outcomes))

        if not overall_corrections:
            return

        win_rate = sum(overall_corrections) / len(overall_corrections)

        if win_rate >= 0.65:
            # Strong performance → slightly lower threshold (more aggressive)
            new_threshold = max(settings.BUY_THRESHOLD_MIN, self.current_threshold - 0.01)
        elif win_rate < 0.50:
            # Poor performance → raise threshold (more conservative)
            new_threshold = min(settings.BUY_THRESHOLD_MAX, self.current_threshold + 0.02)
        else:
            new_threshold = self.current_threshold

        if new_threshold != self.current_threshold:
            old = self.current_threshold
            self.current_threshold = new_threshold
            logger.info(f"🎯 Threshold adjusted: {old:.2f} → {new_threshold:.2f} (win_rate={win_rate:.2f})")

    def get_status(self) -> dict:
        regime_win_rates = {}
        for regime, outcomes in self.regime_outcomes.items():
            if outcomes:
                regime_win_rates[regime] = round(sum(outcomes) / len(outcomes), 3)

        return {
            "current_threshold": self.current_threshold,
            "min_threshold": settings.BUY_THRESHOLD_MIN,
            "max_threshold": settings.BUY_THRESHOLD_MAX,
            "regime_win_rates": regime_win_rates,
        }
