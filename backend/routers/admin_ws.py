"""Websocket endpoints for admin alerts.

Project: Thronestead ©
File: admin_ws.py
Role: API routes for admin websocket.
Version: 2025-06-22
"""

import asyncio
from ..env_utils import get_env_var

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from starlette.websockets import WebSocketState

router = APIRouter()

connected_admins: list[WebSocket] = []


@router.websocket("/api/admin/alerts/live")
async def live_admin_alerts(websocket: WebSocket):
    """Stream live admin alerts once API key verified."""
    api_key = websocket.headers.get("x-api-key")
    if api_key != get_env_var("API_SECRET"):
        await websocket.close(code=1008)
        return

    await websocket.accept()
    connected_admins.append(websocket)
    try:
        while True:
            if websocket.client_state != WebSocketState.CONNECTED:
                break
            await asyncio.sleep(10)
    except WebSocketDisconnect:
        pass
    finally:
        if websocket in connected_admins:
            connected_admins.remove(websocket)
