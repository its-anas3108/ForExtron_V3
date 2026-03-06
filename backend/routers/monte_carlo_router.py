"""
monte_carlo_router.py – POST /api/simulate
Runs Monte Carlo simulation for a given trade setup.
"""

from fastapi import APIRouter
from pydantic import BaseModel, Field
from features.simulator import monte_carlo_simulate

router = APIRouter(tags=["simulator"])


class SimulationRequest(BaseModel):
    pair: str = "EUR_USD"
    direction: str = "BUY"
    entry: float = 1.0850
    sl: float = 1.0820
    tp: float = 1.0910
    volatility: float = Field(default=0.08, description="Annualized volatility estimate")
    num_simulations: int = Field(default=500, ge=100, le=2000)
    horizon_minutes: int = Field(default=120, ge=10, le=480)


@router.post("/simulate")
async def simulate(req: SimulationRequest):
    result = monte_carlo_simulate(
        price=req.entry,
        volatility=req.volatility,
        direction=req.direction,
        sl=req.sl,
        tp=req.tp,
        n_sims=req.num_simulations,
        horizon_steps=req.horizon_minutes,
    )
    result["pair"] = req.pair
    return result
