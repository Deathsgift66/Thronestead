"""
Project: Thronestead ©
File: admin_ws.py
Role: API routes for admin ws.
Version: 2025-06-21
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from starlette.websockets import WebSocketState
import asyncio

router = APIRouter()

connected_admins: list[WebSocket] = []


@router.websocket("/api/admin/alerts/live")
async def live_admin_alerts(websocket: WebSocket):
    # TODO: Missing API key protection
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
