"""Websocket endpoints for admin alerts.

Project: Thronestead ©
File: admin_ws.py
Role: API routes for admin websocket.
Version: 2025-06-22
"""

import asyncio
import json

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException
from starlette.websockets import WebSocketState

from ..database import SessionLocal
from ..security import verify_admin, validate_reauth_token

router = APIRouter()

connected_admins: list[WebSocket] = []


async def broadcast_admin_event(event: dict) -> None:
    """Send ``event`` to all connected admin websocket clients."""
    message = json.dumps(event)
    to_remove: list[WebSocket] = []
    for ws in connected_admins:
        try:
            if ws.client_state == WebSocketState.CONNECTED:
                await ws.send_text(message)
            else:
                to_remove.append(ws)
        except Exception:
            to_remove.append(ws)
    for ws in to_remove:
        if ws in connected_admins:
            connected_admins.remove(ws)


@router.websocket("/api/admin/alerts/live")
async def live_admin_alerts(websocket: WebSocket):
    """Stream live admin alerts once JWT verified as an admin."""
    token = websocket.query_params.get("token")
    user_id = websocket.query_params.get("uid")
    if not token or not user_id:
        await websocket.close(code=1008)
        return

    db = SessionLocal()
    if not validate_reauth_token(db, user_id, token):
        db.close()
        await websocket.close(code=1008)
        return
    try:
        verify_admin(user_id, db)
    except HTTPException:
        db.close()
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
        db.close()
