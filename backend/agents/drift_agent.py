"""
drift_agent.py – Drift Detection & Retrain Trigger Agent.

Monitors:
  - Rolling prediction accuracy
  - Confidence level trend
  - HOLD ratio (proxy for model uncertainty)

Triggers retraining when degradation exceeds thresholds.
"""

import logging
from collections import deque
from datetime import datetime, timezone
from typing import Optional
from app.config import settings

logger = logging.getLogger(__name__)


class DriftAgent:

    def __init__(self, window: int = 100):
        self.window = window
        self.confidences: deque = deque(maxlen=window)
        self.outcomes: deque = deque(maxlen=window)   # 1=correct, 0=wrong
        self.decisions: deque = deque(maxlen=window)  # "BUY"/"SELL"/"HOLD"
        self.retrain_triggered: bool = False
        self.last_trigger_time: Optional[str] = None
        self.baseline_confidence: Optional[float] = None
        self.events: list = []

    def record_prediction(self, confidence: float, decision: str):
        self.confidences.append(confidence)
        self.decisions.append(decision)

        if self.baseline_confidence is None and len(self.confidences) >= 20:
            self.baseline_confidence = sum(list(self.confidences)[:20]) / 20

    def record_outcome(self, was_correct: bool):
        self.outcomes.append(1 if was_correct else 0)

    def check_drift(self) -> dict:
        status = {
            "drift_detected": False,
            "reason": None,
            "rolling_accuracy": None,
            "avg_confidence": None,
            "hold_ratio": None,
            "retrain_triggered": self.retrain_triggered,
        }

        if len(self.confidences) < 20:
            return status

        confidences_list = list(self.confidences)
        decisions_list = list(self.decisions)

        # Current average confidence
        avg_conf = sum(confidences_list) / len(confidences_list)
        status["avg_confidence"] = round(avg_conf, 4)

        # HOLD ratio
        hold_count = decisions_list.count("HOLD")
        hold_ratio = hold_count / len(decisions_list)
        status["hold_ratio"] = round(hold_ratio, 4)

        # Rolling accuracy (if outcome data available)
        if len(self.outcomes) >= 20:
            outcomes_list = list(self.outcomes)
            rolling_acc = sum(outcomes_list) / len(outcomes_list)
            status["rolling_accuracy"] = round(rolling_acc, 4)

        # Drift conditions
        if self.baseline_confidence and avg_conf < (self.baseline_confidence - settings.DRIFT_DROP_THRESHOLD):
            status["drift_detected"] = True
            status["reason"] = (
                f"Confidence dropped {(self.baseline_confidence - avg_conf)*100:.1f}% "
                f"from baseline {self.baseline_confidence:.3f} → {avg_conf:.3f}"
            )

        if hold_ratio > settings.HOLD_RATIO_THRESHOLD:
            status["drift_detected"] = True
            status["reason"] = status.get("reason", "") + f" | HOLD ratio {hold_ratio*100:.0f}% > 60%"

        if status["drift_detected"] and not self.retrain_triggered:
            self.retrain_triggered = True
            self.last_trigger_time = datetime.now(timezone.utc).isoformat()
            self._log_event("RETRAIN_TRIGGERED", status["reason"])
            logger.warning(f"🔁 Drift Agent: Retrain triggered. {status['reason']}")

        return status

    def reset_trigger(self):
        """Call after successful retraining."""
        self.retrain_triggered = False
        self.baseline_confidence = None
        self.confidences.clear()
        self.decisions.clear()
        self._log_event("TRIGGER_RESET", "Retrain complete, drift state reset")

    def get_status(self) -> dict:
        return {
            **self.check_drift(),
            "window": self.window,
            "samples_collected": len(self.confidences),
            "baseline_confidence": self.baseline_confidence,
            "last_trigger_time": self.last_trigger_time,
        }

    def _log_event(self, event: str, detail: str):
        self.events.append({
            "agent": "drift_agent",
            "event": event,
            "detail": detail,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })
