from __future__ import annotations

from typing import Any

from fastapi import WebSocket


class ConnectionManager:
    """Manage active KAIJU WebSocket connections and broadcasts."""

    def __init__(self) -> None:
        self.active_connections: set[WebSocket] = set()

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self.active_connections.add(websocket)

    def disconnect(self, websocket: WebSocket) -> None:
        self.active_connections.discard(websocket)

    async def send_personal(self, websocket: WebSocket, event: dict[str, Any]) -> None:
        await websocket.send_json(event)

    async def broadcast(self, event: dict[str, Any]) -> None:
        disconnected: list[WebSocket] = []

        for connection in self.active_connections:
            try:
                await connection.send_json(event)
            except Exception:
                disconnected.append(connection)

        for connection in disconnected:
            self.disconnect(connection)


manager = ConnectionManager()


async def publish_event(
    event_type: str,
    data: dict[str, Any],
) -> None:
    """Broadcast a typed KAIJU event to all connected clients."""
    await manager.broadcast(
        {
            "type": event_type,
            "data": data,
        }
    )