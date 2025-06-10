from typing import Optional
from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from ..database import get_db
from services.audit_service import fetch_filtered_logs, fetch_user_related_logs

router = APIRouter(prefix="/api/admin/audit-log", tags=["admin_audit"])

@router.get("")
def get_audit_logs(
    user_id: Optional[str] = None,
    action: Optional[str] = None,
    date_from: Optional[datetime] = Query(None),
    date_to: Optional[datetime] = Query(None),
    limit: int = 100,
    db: Session = Depends(get_db),
):
    """Return filtered audit logs."""
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
def get_user_logs(user_id: str, db: Session = Depends(get_db)):
    """Return logs from multiple tables related to a user."""
    return fetch_user_related_logs(db, user_id)
