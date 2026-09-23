from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect

from app.auth.security import JWT_ALGORITHM, JWT_SECRET_KEY
from app.websocket.manager import manager
import jwt


router = APIRouter(tags=["WebSocket"])


def authenticate_websocket(token: str | None) -> int | None:
    """Return the authenticated user id from a JWT token."""
    if not token:
        return None

    try:
        payload = jwt.decode(
            token,
            JWT_SECRET_KEY,
            algorithms=[JWT_ALGORITHM],
        )

        user_id = payload.get("sub")

        if user_id is None:
            return None

        return int(user_id)

    except (jwt.InvalidTokenError, TypeError, ValueError):
        return None


@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    token: str | None = Query(default=None),
) -> None:
    """
    Real-time KAIJU event stream.

    The JWT is provided through the `token` query parameter because
    browser WebSocket clients cannot use the normal HTTP Authorization
    dependency in the same way as REST requests.
    """
    user_id = authenticate_websocket(token)

    if user_id is None:
        await websocket.close(code=1008, reason="Authentication required")
        return

    await manager.connect(websocket)

    await manager.send_personal(
        websocket,
        {
            "type": "CONNECTED",
            "data": {
                "user_id": user_id,
                "message": "Connected to KAIJU real-time events.",
            },
        },
    )

    try:
        while True:
            await websocket.receive_text()

    except WebSocketDisconnect:
        manager.disconnect(websocket)