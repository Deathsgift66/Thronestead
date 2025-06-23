# Project Name: Thronestead©
# File Name: admin_audit_log.py
# Version: 6.13.2025.19.49 (Patched)
# Developer: Deathsgift66

"""
Admin-only endpoints for accessing and streaming audit logs.
Supports filtered log queries, user-specific tracing, and live SSE feeds.
"""

import json
import asyncio
import logging
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from ..database import get_db
from ..security import require_user_id, verify_api_key
from .admin_dashboard import verify_admin
from services.audit_service import fetch_filtered_logs, fetch_user_related_logs

router = APIRouter(prefix="/api/admin/audit-log", tags=["admin_audit"])
logger = logging.getLogger("Thronestead.AdminAudit")


# -------------------------
# 🔍 Filtered Audit Logs
# -------------------------
@router.get("/")
def get_audit_logs(
    user_id: Optional[str] = None,
    action: Optional[str] = None,
    date_from: Optional[datetime] = Query(None),
    date_to: Optional[datetime] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    verify: str = Depends(verify_api_key),
    admin_user_id: str = Depends(require_user_id),
    db: Session = Depends(get_db),
):
    """
    Return filtered audit log entries.

    Query Params:
        - user_id: Filter by affected user
        - action: Filter by audit action type
        - date_from/date_to: Limit time range
        - limit: Maximum rows (default: 100, max: 1000)
    """
    verify_admin(admin_user_id, db)
    logger.info(
        f"🔎 Admin {admin_user_id} fetched audit logs (user={user_id}, action={action})"
    )
    logs = fetch_filtered_logs(
        db,
        user_id=user_id,
        action=action,
        date_from=date_from,
        date_to=date_to,
        limit=limit,
    )
    return {"logs": logs}


# -------------------------
# 👤 User-Specific Log View
# -------------------------
@router.get("/user/{user_id}")
def get_user_logs(
    user_id: str,
    verify: str = Depends(verify_api_key),
    admin_user_id: str = Depends(require_user_id),
    db: Session = Depends(get_db),
):
    """Return logs from all systems related to a specific user ID."""
    verify_admin(admin_user_id, db)
    logger.info(f"📄 Admin {admin_user_id} fetched logs for user {user_id}")
    return fetch_user_related_logs(db, user_id)


# -------------------------
# 📡 Server-Sent Event Stream (Live Feed)
# -------------------------
@router.get("/stream", response_class=StreamingResponse)
async def stream_logs(
    verify: str = Depends(verify_api_key),
    admin_user_id: str = Depends(require_user_id),
    db: Session = Depends(get_db),
):
    """
    Stream recent audit log entries using Server-Sent Events (SSE).
    Emits latest log every 5 seconds.
    """
    verify_admin(admin_user_id, db)
    logger.info(f"🛰️ Admin {admin_user_id} connected to audit log stream.")

    async def event_generator():
        last_id: Optional[int] = None
        while True:
            logs = fetch_filtered_logs(db, limit=1)
            if logs:
                latest = logs[0]
                if latest.get("log_id") != last_id:
                    last_id = latest.get("log_id")
                    data = json.dumps(latest, default=str)
                    yield f"data: {data}\n\n"
            await asyncio.sleep(5)

    return StreamingResponse(event_generator(), media_type="text/event-stream")
