"""
main.py – FastAPI application entry point for ForEX Pro
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import asyncio
import logging

from app.config import settings
from app.websocket_manager import manager
from database.crud import init_db
from data.stream_handler import StreamHandler
from agents.supervisor import SupervisorAgent

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

stream_handler = StreamHandler()
supervisor = SupervisorAgent()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown lifecycle."""
    logger.info("🚀 ForEX Pro starting up...")
    await init_db()
    # Start background streaming tasks for default instrument
    asyncio.create_task(stream_handler.start(settings.DEFAULT_INSTRUMENT))
    asyncio.create_task(supervisor.run_loop())
    logger.info(f"✅ Streaming started for {settings.DEFAULT_INSTRUMENT}")
    yield
    logger.info("🛑 ForEX Pro shutting down...")
    await stream_handler.stop()


app = FastAPI(
    title="ForEX Pro – Institutional AI Forex Platform",
    version="2.0.0",
    description="Live-data, multi-agent, institutional-grade Forex intelligence.",
    lifespan=lifespan,
)

# ── CORS ─────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ───────────────────────────────────────────────────────────────────
from routers import signal_router, performance_router, regime_router, chat_router, execution_router, agents_router, explain_router
from routers import monte_carlo_router, news_router, replay_router, xai_router, recovery_router, currency_router, liquidity_router
from routers import auth_router, account_router

app.include_router(auth_router.router, prefix="/api")
app.include_router(account_router.router, prefix="/api")
app.include_router(signal_router.router, prefix="/api")
app.include_router(performance_router.router, prefix="/api")
app.include_router(regime_router.router, prefix="/api")
app.include_router(chat_router.router, prefix="/api")
app.include_router(execution_router.router, prefix="/api")
app.include_router(agents_router.router, prefix="/api")
app.include_router(explain_router.router, prefix="/api")
app.include_router(monte_carlo_router.router, prefix="/api")
app.include_router(news_router.router, prefix="/api")
app.include_router(replay_router.router, prefix="/api")
app.include_router(xai_router.router, prefix="/api")
app.include_router(recovery_router.router, prefix="/api")
app.include_router(currency_router.router, prefix="/api")
app.include_router(liquidity_router.router, prefix="/api")


# ── WebSocket endpoint ────────────────────────────────────────────────────────
@app.websocket("/ws/live/{instrument}")
async def websocket_live(websocket: WebSocket, instrument: str):
    """Live candle + signal push for a given instrument."""
    await manager.connect(websocket, instrument)
    try:
        while True:
            # Keep connection alive; data is pushed from stream_handler
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket, instrument)


@app.websocket("/ws/agents")
async def websocket_agents(websocket: WebSocket):
    """Real-time agent event stream."""
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)


@app.get("/health")
async def health():
    return {"status": "ok", "version": "2.0.0", "instruments": settings.INSTRUMENTS}

import os
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

frontend_dist = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../frontend/dist"))
if os.path.isdir(frontend_dist):
    app.mount("/assets", StaticFiles(directory=os.path.join(frontend_dist, "assets")), name="assets")
    
    @app.get("/{full_path:path}")
    async def serve_react_app(full_path: str):
        if full_path.startswith("api/") or full_path.startswith("ws/"):
            from fastapi import HTTPException
            raise HTTPException(status_code=404, detail="Not Found")
        file_path = os.path.join(frontend_dist, full_path)
        if file_path != frontend_dist and os.path.isfile(file_path):
            return FileResponse(file_path)
        return FileResponse(os.path.join(frontend_dist, "index.html"))
