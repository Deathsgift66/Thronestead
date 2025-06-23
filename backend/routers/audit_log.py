# Project Name: Thronestead©
# File Name: audit_log.py
# Version: 6.20.2025.22.45
# Developer: Deathsgift66

"""
Project: Thronestead ©
File: audit_log.py
Role: API routes for audit log.
Version: 2025-06-21
"""

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from services.audit_service import fetch_logs, log_action

from ..database import get_db
from ..security import verify_jwt_token

# FastAPI router for system-wide audit logs
router = APIRouter(prefix="/api/audit-log", tags=["audit_log"])


# Request body for logging a new action
class LogPayload(BaseModel):
    user_id: str | None = None
    kingdom_id: int | None = None
    action: str
    details: str


@router.get("/")
def get_audit_logs(
    user_id: str | None = Query(None, description="Filter logs by user ID"),
    kingdom_id: int | None = Query(None, description="Filter logs by Kingdom ID"),
    limit: int = Query(100, ge=1, le=500, description="Max number of logs to return"),
    _uid: str = Depends(verify_jwt_token),
    db: Session = Depends(get_db),
):
    """
    Retrieve audit logs from the system.

    - Optional `user_id` filters logs for a specific user.
    - Optional `kingdom_id` filters logs for a specific kingdom.
    - `limit` controls the number of logs returned (default: 100).
    """
    logs = fetch_logs(db, user_id=user_id, kingdom_id=kingdom_id, limit=limit)
    return {"logs": logs}


@router.post("/")
def create_audit_log(
    payload: LogPayload,
    _uid: str = Depends(verify_jwt_token),
    db: Session = Depends(get_db),
):
    """
    Create a new audit log entry.

    - `user_id`: (optional) UUID of the acting user.
    - `kingdom_id`: (optional) ID of the affected kingdom.
    - `action`: Required string describing the action taken.
    - `details`: Required string describing what occurred.
    """
    log_action(
        db,
        user_id=payload.user_id,
        action=payload.action,
        details=payload.details,
        kingdom_id=payload.kingdom_id,
    )
    return {"message": "Action logged successfully."}
