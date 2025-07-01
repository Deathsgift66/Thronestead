# Comment
# Project Name: Thronestead©
# File Name: account_export.py
# Version: 7/1/2025 10:31
# Developer: Deathsgift66
"""
Project: Thronestead ©
File: account_export.py
Role: API route for exporting account data.
Version: 2025-06-21
"""

from __future__ import annotations

import io
import json
import zipfile

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy import text
from sqlalchemy.orm import Session

from ..database import get_db
from ..security import verify_jwt_token

router = APIRouter(prefix="/api/account", tags=["account"])


@router.get("/export")
def export_account(user_id: str = Depends(verify_jwt_token), db: Session = Depends(get_db)):
    """Return a zip file containing all data related to the current user."""
    user_row = (
        db.execute(text("SELECT * FROM users WHERE user_id = :uid"), {"uid": user_id})
        .mappings()
        .fetchone()
    )
    if not user_row:
        raise HTTPException(status_code=404, detail="User not found")
    user = dict(user_row)

    kingdom = None
    kingdom_id = user.get("kingdom_id")
    if kingdom_id:
        k_row = (
            db.execute(text("SELECT * FROM kingdoms WHERE kingdom_id = :kid"), {"kid": kingdom_id})
            .mappings()
            .fetchone()
        )
        if k_row:
            kingdom = dict(k_row)

    msg_rows = (
        db.execute(
            text(
                "SELECT * FROM player_messages WHERE user_id = :uid OR recipient_id = :uid"
            ),
            {"uid": user_id},
        )
        .mappings()
        .fetchall()
    )
    messages = [dict(r) for r in msg_rows]

    audit_rows = (
        db.execute(text("SELECT * FROM audit_log WHERE user_id = :uid"), {"uid": user_id})
        .mappings()
        .fetchall()
    )
    audit_logs = [dict(r) for r in audit_rows]

    troops = []
    if kingdom_id:
        troop_rows = (
            db.execute(text("SELECT * FROM kingdom_troops WHERE kingdom_id = :kid"), {"kid": kingdom_id})
            .mappings()
            .fetchall()
        )
        troops = [dict(r) for r in troop_rows]

    payload = {
        "user": user,
        "kingdom": kingdom,
        "messages": messages,
        "audit_logs": audit_logs,
        "troops": troops,
    }

    json_bytes = json.dumps(payload, default=str).encode()
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("data.json", json_bytes)
    buffer.seek(0)
    return Response(buffer.getvalue(), media_type="application/zip")

