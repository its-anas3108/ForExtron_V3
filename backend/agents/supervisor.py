"""
supervisor.py – Master Agentic Supervisor.
Coordinates Risk Guardian, Drift Agent, Threshold Agent, and Data Integrity Agent.
Runs as an async background loop.
"""

import asyncio
import logging
from datetime import datetime, timezone

from agents.risk_guardian import RiskGuardianAgent
from agents.drift_agent import DriftAgent
from agents.threshold_agent import ThresholdAgent
from app.websocket_manager import manager

logger = logging.getLogger(__name__)


class SupervisorAgent:
    """
    Master coordinator: polls all sub-agents every 30 seconds,
    broadcasts aggregated health status via WebSocket.
    """

    def __init__(self):
        self.risk_guardian = RiskGuardianAgent()
        self.drift_agent = DriftAgent()
        self.threshold_agent = ThresholdAgent()
        self.running = False
        self.last_status: dict = {}

    async def run_loop(self, interval: int = 30):
        """Background task: check agents and broadcast status."""
        self.running = True
        logger.info("🤖 Supervisor Agent started")
        while self.running:
            try:
                status = self.get_aggregate_status()
                self.last_status = status
                await manager.broadcast_agent_event(status)

                # Check if drift requires retraining
                if status["drift"]["retrain_triggered"]:
                    logger.warning("🔁 Supervisor: Drift detected, initiating retrain...")
                    asyncio.create_task(self._trigger_retrain())

                await asyncio.sleep(interval)
            except Exception as e:
                logger.error(f"Supervisor loop error: {e}", exc_info=True)
                await asyncio.sleep(5)

    async def _trigger_retrain(self):
        """Async retrain in background."""
        try:
            from retraining.retrain_pipeline import RetrainPipeline
            pipeline = RetrainPipeline()
            result = await asyncio.get_event_loop().run_in_executor(None, pipeline.run)
            if result.get("success"):
                self.drift_agent.reset_trigger()
                logger.info("✅ Supervisor: Retraining complete, drift state reset")
            else:
                logger.warning(f"⚠️ Supervisor: Retraining failed: {result.get('error')}")
        except Exception as e:
            logger.error(f"Retrain pipeline error: {e}")

    def get_aggregate_status(self) -> dict:
        drift_status = self.drift_agent.check_drift()
        risk_status = self.risk_guardian.get_status()
        threshold_status = self.threshold_agent.get_status()

        overall_healthy = (
            not risk_status["hold_mode"]
            and not drift_status["drift_detected"]
        )

        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "overall_healthy": overall_healthy,
            "risk": risk_status,
            "drift": drift_status,
            "threshold": threshold_status,
            "system_mode": "HOLD" if risk_status["hold_mode"] else "ACTIVE",
        }

    def approve_decision(self, decision: str) -> dict:
        """
        Final gate before a signal is emitted.
        Returns approval status with reason.
        """
        if decision in ("BUY", "SELL"):
            approved, reason = self.risk_guardian.approve_trade()
            return {"approved": approved, "reason": reason}
        return {"approved": True, "reason": "HOLD requires no approval"}
