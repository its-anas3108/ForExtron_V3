"""
context_builder.py – Assembles context dict for LLM prompt injection.
"""

import logging
from app.config import settings
from database.crud import get_latest_signal, get_metrics

logger = logging.getLogger(__name__)


async def build_context(instrument: str, supervisor=None) -> dict:
    """Fetch all relevant context for the chatbot from DB and live agents."""
    context = {}

    # Latest signal
    try:
        context["latest_signal"] = await get_latest_signal(instrument) or {}
        context["regime"] = context["latest_signal"].get("regime", "unknown")
    except Exception as e:
        logger.warning(f"Context: signal fetch failed: {e}")
        context["latest_signal"] = {}
        context["regime"] = "unknown"

    # Performance metrics
    try:
        context["performance"] = await get_metrics(instrument) or {}
    except Exception as e:
        logger.warning(f"Context: metrics fetch failed: {e}")
        context["performance"] = {}

    # Risk / Agent status
    if supervisor:
        try:
            context["risk_status"] = supervisor.risk_guardian.get_status()
            context["drift_status"] = supervisor.drift_agent.get_status()
            context["threshold_status"] = supervisor.threshold_agent.get_status()
            context["agent_health"] = supervisor.get_aggregate_status()
        except Exception as e:
            logger.warning(f"Context: agent status failed: {e}")

    context["instrument"] = instrument
    return context
