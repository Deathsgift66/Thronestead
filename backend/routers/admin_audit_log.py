from typing import Optional
from datetime import datetime
import json
import asyncio

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from ..database import get_db
from services.audit_service import fetch_filtered_logs, fetch_user_related_logs
from .admin_dashboard import verify_admin
from ..security import require_user_id

router = APIRouter(prefix="/api/admin/audit-log", tags=["admin_audit"])

@router.get("")
def get_audit_logs(
    user_id: Optional[str] = None,
    action: Optional[str] = None,
    date_from: Optional[datetime] = Query(None),
    date_to: Optional[datetime] = Query(None),
    limit: int = 100,
    admin_user_id: str = Depends(require_user_id),
    db: Session = Depends(get_db),
):
    """Return filtered audit logs."""
    verify_admin(admin_user_id, db)
    logs = fetch_filtered_logs(
        db,
        user_id=user_id,
        action=action,
        date_from=date_from,
        date_to=date_to,
        limit=limit,
    )
    return {"logs": logs}


@router.get("/user/{user_id}")
def get_user_logs(
    user_id: str,
    admin_user_id: str = Depends(require_user_id),
    db: Session = Depends(get_db),
):
    """Return logs from multiple tables related to a user."""
    verify_admin(admin_user_id, db)
    return fetch_user_related_logs(db, user_id)


@router.get("/stream")
async def stream_logs(
    admin_user_id: str = Depends(require_user_id),
    db: Session = Depends(get_db),
):
    """Stream the latest audit log entries using server-sent events."""
    verify_admin(admin_user_id, db)

    async def event_generator():
        last_id: int | None = None
        while True:
            logs = fetch_filtered_logs(db, limit=1)
            if logs:
                log = logs[0]
                if log["log_id"] != last_id:
                    last_id = log["log_id"]
                    data = json.dumps(log, default=str)
                    yield f"data: {data}\n\n"
            await asyncio.sleep(5)

    return StreamingResponse(event_generator(), media_type="text/event-stream")
