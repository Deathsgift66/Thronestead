# Project Name: Kingmakers Rise©
# File Name: audit_log.py
# Version 6.13.2025.19.49
# Developer: Deathsgift66
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from ..database import get_db
from services.audit_service import fetch_logs, log_action
from pydantic import BaseModel

router = APIRouter(prefix="/api/audit-log", tags=["audit_log"])


class LogPayload(BaseModel):
    user_id: str | None = None
    action: str
    details: str


@router.get("")
def audit_log(
    user_id: str | None = Query(None),
    limit: int = 100,
    db: Session = Depends(get_db),
):
    """Return audit logs, optionally filtered by player."""
    logs = fetch_logs(db, user_id=user_id, limit=limit)
    return {"logs": logs}


@router.post("")
def create_log(payload: LogPayload, db: Session = Depends(get_db)):
    """Insert a new audit log entry."""
    log_action(db, payload.user_id, payload.action, payload.details)
    return {"message": "logged"}

