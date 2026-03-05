"""
websocket_manager.py – Manages active WebSocket connections and broadcasts live data.
"""

from typing import Dict, List
from fastapi import WebSocket
import json
import logging

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages multiple WebSocket client connections per instrument."""

    def __init__(self):
        # instrument → list of connected websocket clients
        self.active_connections: Dict[str, List[WebSocket]] = {}
        # global connections (receive all instruments)
        self.global_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket, instrument: str = None):
        await websocket.accept()
        if instrument:
            if instrument not in self.active_connections:
                self.active_connections[instrument] = []
            self.active_connections[instrument].append(websocket)
            logger.info(f"Client connected for instrument: {instrument}")
        else:
            self.global_connections.append(websocket)
            logger.info("Global client connected")

    def disconnect(self, websocket: WebSocket, instrument: str = None):
        if instrument and instrument in self.active_connections:
            self.active_connections[instrument] = [
                c for c in self.active_connections[instrument] if c != websocket
            ]
        elif websocket in self.global_connections:
            self.global_connections.remove(websocket)
        logger.info(f"Client disconnected ({instrument or 'global'})")

    async def broadcast_candle(self, instrument: str, candle_data: dict):
        """Broadcast a closed candle to all subscribers of that instrument."""
        message = json.dumps({"type": "candle", "instrument": instrument, "data": candle_data})
        dead = []
        connections = self.active_connections.get(instrument, []) + self.global_connections
        for connection in connections:
            try:
                await connection.send_text(message)
            except Exception:
                dead.append(connection)
        for d in dead:
            self.disconnect(d, instrument)

    async def broadcast_signal(self, instrument: str, signal_data: dict):
        """Broadcast a new trading signal."""
        message = json.dumps({"type": "signal", "instrument": instrument, "data": signal_data})
        connections = self.active_connections.get(instrument, []) + self.global_connections
        for connection in connections:
            try:
                await connection.send_text(message)
            except Exception:
                pass

    async def broadcast_agent_event(self, event: dict):
        """Broadcast agent status events to all global connections."""
        message = json.dumps({"type": "agent_event", "data": event})
        for connection in self.global_connections:
            try:
                await connection.send_text(message)
            except Exception:
                pass

    async def send_personal(self, websocket: WebSocket, data: dict):
        await websocket.send_text(json.dumps(data))


manager = ConnectionManager()
