import asyncio
import json
from typing import Dict, Set, Optional
from fastapi import WebSocket
from backend.app.core.logger import logger


class WebSocketConnectionManager:
    """
    Thread-safe WebSocket Connection and Room Hub.
    Manages active subscriptions for real-time delivery tracking rooms
    and streaming driver telemetry broadcasts.
    """

    def __init__(self):
        # Maps delivery_id -> Set of connected WebSockets (customers, admins)
        self.delivery_rooms: Dict[int, Set[WebSocket]] = {}
        # Maps driver_id -> WebSocket connection
        self.driver_connections: Dict[int, WebSocket] = {}
        self._lock = asyncio.Lock()

    async def connect_delivery(self, websocket: WebSocket, delivery_id: int):
        """Accepts and registers client subscription to a delivery's live tracking room."""
        await websocket.accept()
        async with self._lock:
            if delivery_id not in self.delivery_rooms:
                self.delivery_rooms[delivery_id] = set()
            self.delivery_rooms[delivery_id].add(websocket)
        logger.info(f"WebSocket client connected to delivery room {delivery_id}. Total listeners: {len(self.delivery_rooms[delivery_id])}")

    async def disconnect_delivery(self, websocket: WebSocket, delivery_id: int):
        """Removes disconnected client from delivery tracking room."""
        async with self._lock:
            if delivery_id in self.delivery_rooms:
                self.delivery_rooms[delivery_id].discard(websocket)
                if not self.delivery_rooms[delivery_id]:
                    del self.delivery_rooms[delivery_id]
        logger.info(f"WebSocket client disconnected from delivery room {delivery_id}")

    async def connect_driver(self, websocket: WebSocket, driver_id: int):
        """Accepts and registers driver's real-time telemetry broadcaster."""
        await websocket.accept()
        async with self._lock:
            self.driver_connections[driver_id] = websocket
        logger.info(f"Driver {driver_id} connected live telemetry broadcaster")

    async def disconnect_driver(self, driver_id: int):
        """Removes driver broadcaster connection."""
        async with self._lock:
            if driver_id in self.driver_connections:
                del self.driver_connections[driver_id]
        logger.info(f"Driver {driver_id} disconnected telemetry broadcaster")

    async def broadcast_to_delivery(self, delivery_id: int, message: dict):
        """Broadcasts real-time coordinates, ETA, and delay updates to all subscribers of a delivery."""
        async with self._lock:
            listeners = list(self.delivery_rooms.get(delivery_id, []))

        if not listeners:
            return

        dead_sockets = []
        payload = json.dumps(message)

        for ws in listeners:
            try:
                await ws.send_text(payload)
            except Exception as exc:
                logger.warning(f"Failed sending WS packet to client in room {delivery_id}: {exc}")
                dead_sockets.append(ws)

        if dead_sockets:
            async with self._lock:
                if delivery_id in self.delivery_rooms:
                    for dead_ws in dead_sockets:
                        self.delivery_rooms[delivery_id].discard(dead_ws)

    async def broadcast_all(self, message: dict):
        """Broadcasts a global message to all currently connected clients across all rooms."""
        payload = json.dumps(message)
        async with self._lock:
            all_sockets = [
                ws for room in self.delivery_rooms.values() for ws in room
            ] + list(self.driver_connections.values())

        for ws in all_sockets:
            try:
                await ws.send_text(payload)
            except Exception:
                pass


# Global singleton instance
ws_manager = WebSocketConnectionManager()
