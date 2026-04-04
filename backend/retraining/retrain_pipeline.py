"""
retrain_pipeline.py – Automated model retraining triggered by Drift Agent.
Temporarily disabled pending Forextron-TFT hybrid integration.
"""

import logging
from datetime import datetime, timezone
from app.config import settings

logger = logging.getLogger(__name__)

class RetrainPipeline:

    def run(self, instrument: str = None) -> dict:
        """Synchronous retrain method (run via executor)."""
        logger.warning("🔁 Retrain pipeline is disabled pending ForextronTFTTrainer integration")
        return {
            "success": False,
            "error": "Pipeline disabled for Forextron-TFT model upgrade",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "instruments": [instrument] if instrument else settings.INSTRUMENTS[:3],
        }
