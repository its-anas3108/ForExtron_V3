"""
agents_router.py – GET /api/agents/status
"""

from fastapi import APIRouter
from database.crud import get_agent_logs

router = APIRouter(tags=["agents"])


@router.get("/agents/status")
async def get_agent_status():
    from app.main import supervisor
    return supervisor.get_aggregate_status()


@router.get("/agents/logs")
async def get_logs(limit: int = 50):
    return await get_agent_logs(limit=limit)
