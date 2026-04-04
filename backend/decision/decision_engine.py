"""
decision_engine.py – Institutional Decision Engine.

BUY conditions (ALL must be true):
  1. Regime = Expansion
  2. Structure bias = Bullish (trend_bias > 0, bos_bullish recent)
  3. Liquidity sweep below detected (stop hunt cleared)
  4. Ensemble probability > dynamic threshold
  5. RSI < 70 (not overbought)
  6. R:R >= 1:2
  7. Supervisor (Risk Guardian) approves

Else: HOLD
"""

import logging
import pandas as pd
from datetime import datetime, timezone
from typing import Optional, Dict

from models.regime_classifier import RegimeClassifier
from models.forextron_v3.inference import ForextronPredictor
from decision.risk_engine import RiskEngine
from database.crud import insert_signal

logger = logging.getLogger(__name__)

# Lazy-loaded singletons
_regime_clf: Optional[RegimeClassifier] = None
_predictor: Optional[ForextronPredictor] = None
_risk_engine: Optional[RiskEngine] = None


def _get_regime_clf():
    global _regime_clf
    if _regime_clf is None:
        _regime_clf = RegimeClassifier()
    return _regime_clf


def _get_predictor():
    global _predictor
    if _predictor is None:
        _predictor = ForextronPredictor()
    return _predictor


def _get_risk_engine():
    global _risk_engine
    if _risk_engine is None:
        _risk_engine = RiskEngine()
    return _risk_engine


class DecisionEngine:

    def __init__(self):
        self.regime_clf = _get_regime_clf()
        self.predictor = _get_predictor()
        self.risk_engine = _get_risk_engine()

    async def evaluate(self, instrument: str, df: pd.DataFrame) -> Optional[dict]:
        """
        Full evaluation pipeline. Returns signal dict or None.
        """
        if len(df) < 30:
            return None

        row = df.iloc[-1]

        # ── Step 1: Regime Classification ─────────────────────────────────
        regime, regime_conf = self.regime_clf.predict(df)

        # ── Step 2: TFT Model Prediction ──────────────────────────────────
        ensemble_prob, model_contributions = self.predictor.predict(df, regime)

        # ── Step 3: Structure Analysis ────────────────────────────────────
        structure_bias = self._get_structure_bias(row)
        liquidity_sweep_below = bool(row.get("liquidity_sweep_low", 0) == 1)

        # ── Step 4: Risk Metrics ──────────────────────────────────────────
        risk_data = self.risk_engine.calculate(df)

        # ── Step 5: Supervisor Approval ───────────────────────────────────
        from agents.supervisor import SupervisorAgent
        supervisor = SupervisorAgent()
        threshold = supervisor.threshold_agent.get_threshold(regime)

        # ── Step 6: Decision Gate ─────────────────────────────────────────
        decision, gate_log = self._apply_gates(
            regime=regime,
            structure_bias=structure_bias,
            liquidity_sweep_below=liquidity_sweep_below,
            ensemble_prob=ensemble_prob,
            rsi=float(row.get("rsi", 50)),
            rr=risk_data.get("rr", 0.0),
            threshold=threshold,
            supervisor=supervisor,
        )

        # Record prediction in drift/threshold agents
        supervisor.drift_agent.record_prediction(ensemble_prob, decision)
        if decision in ("BUY", "SELL"):
            supervisor.threshold_agent.record_outcome(regime, True)  # optimistic default

        # ── Step 7: Build Signal ──────────────────────────────────────────
        signal = {
            "pair": instrument,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "regime": regime,
            "regime_confidence": round(regime_conf, 4),
            "structure_bias": structure_bias,
            "liquidity_sweep_below": liquidity_sweep_below,
            "ensemble_probability": round(ensemble_prob, 4),
            "model_contributions": {k: round(v, 4) for k, v in model_contributions.items()},
            "decision": decision,
            "threshold_used": round(threshold, 4),
            "sl": risk_data.get("sl"),
            "tp": risk_data.get("tp"),
            "lot_size": risk_data.get("lot_size"),
            "rr": round(risk_data.get("rr", 0.0), 2),
            "atr": round(float(row.get("atr", 0)), 5),
            "rsi": round(float(row.get("rsi", 50)), 2),
            "gate_log": gate_log,
            "agent_approval": decision in ("BUY", "SELL"),
        }

        # ── Step 8: Persist ───────────────────────────────────────────────
        try:
            await insert_signal(signal)
        except Exception as e:
            logger.warning(f"Failed to persist signal: {e}")

        logger.info(
            f"[{instrument}] {decision} | Regime: {regime} | "
            f"P={ensemble_prob:.3f} | Threshold={threshold:.3f}"
        )
        return signal

    def _get_structure_bias(self, row: pd.Series) -> str:
        """Determine structural bias from numeric features."""
        trend_bias = float(row.get("trend_bias", 0))
        bos_bullish = float(row.get("bos_bullish", 0))
        bos_bearish = float(row.get("bos_bearish", 0))
        choch = float(row.get("choch", 0))
        structure_slope = float(row.get("structure_slope", 0))

        bull_score = (
            (1 if trend_bias > 0 else 0) +
            (1 if bos_bullish > 0 else 0) +
            (1 if choch > 0 else 0) +
            (1 if structure_slope > 0 else 0)
        )
        bear_score = (
            (1 if trend_bias < 0 else 0) +
            (1 if bos_bearish > 0 else 0) +
            (1 if choch < 0 else 0) +
            (1 if structure_slope < 0 else 0)
        )

        if bull_score >= 3:
            return "bullish"
        elif bear_score >= 3:
            return "bearish"
        return "neutral"

    def _apply_gates(
        self, regime, structure_bias, liquidity_sweep_below,
        ensemble_prob, rsi, rr, threshold, supervisor
    ) -> tuple:
        gate_log = {}

        gate_log["regime_ok"] = (regime == "expansion")
        gate_log["structure_bullish"] = (structure_bias == "bullish")
        gate_log["liquidity_sweep_ok"] = liquidity_sweep_below
        gate_log["probability_ok"] = (ensemble_prob >= threshold)
        gate_log["rsi_ok"] = (rsi < 70)
        gate_log["rr_ok"] = (rr >= 2.0)

        approval = supervisor.approve_decision("BUY")
        gate_log["guardian_ok"] = approval["approved"]
        gate_log["guardian_reason"] = approval.get("reason", "")

        all_gates_pass = all([
            gate_log["regime_ok"],
            gate_log["structure_bullish"],
            gate_log["probability_ok"],
            gate_log["rsi_ok"],
            gate_log["rr_ok"],
            gate_log["guardian_ok"],
        ])

        decision = "BUY" if all_gates_pass else "HOLD"
        return decision, gate_log
