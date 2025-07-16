"""Websocket endpoints for admin alerts.

Project: Thronestead ©
File: admin_ws.py
Role: API routes for admin websocket.
Version: 2025-06-22
"""

import asyncio
from jose import JWTError

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException
from starlette.websockets import WebSocketState

from ..database import SessionLocal
from ..security import decode_supabase_jwt, verify_admin

router = APIRouter()

connected_admins: list[WebSocket] = []


@router.websocket("/api/admin/alerts/live")
async def live_admin_alerts(websocket: WebSocket):
    """Stream live admin alerts once JWT verified as an admin."""
    token = websocket.query_params.get("token")
    if not token:
        await websocket.close(code=1008)
        return

    try:
        claims = decode_supabase_jwt(token)
    except JWTError:
        await websocket.close(code=1008)
        return

    user_id = claims.get("sub")
    if not user_id:
        await websocket.close(code=1008)
        return

    db = SessionLocal()
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
