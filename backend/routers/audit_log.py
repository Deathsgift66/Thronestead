# Project Name: Kingmakers Rise©
# File Name: audit_log.py
# Version: 6.13.2025.20.15
# Developer: Deathsgift66

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..database import get_db
from services.audit_service import fetch_logs, log_action

# FastAPI router for system-wide audit logs
router = APIRouter(prefix="/api/audit-log", tags=["audit_log"])

# Request body for logging a new action
class LogPayload(BaseModel):
    user_id: str | None = None
    action: str
    details: str


@router.get("/")
def get_audit_logs(
    user_id: str | None = Query(None, description="Filter logs by user ID"),
    limit: int = Query(100, ge=1, le=500, description="Max number of logs to return"),
    db: Session = Depends(get_db),
):
    """
    Retrieve audit logs from the system.

    - Optional `user_id` filters logs for a specific user.
    - `limit` controls the number of logs returned (default: 100).
    """
    logs = fetch_logs(db, user_id=user_id, limit=limit)
    return {"logs": logs}


@router.post("/")
def create_audit_log(payload: LogPayload, db: Session = Depends(get_db)):
    """
    Create a new audit log entry.

    - `user_id`: (optional) UUID of the acting user.
    - `action`: Required string describing the action taken.
    - `details`: Required string describing what occurred.
    """
    log_action(db, payload.user_id, payload.action, payload.details)
    return {"message": "Action logged successfully."}
