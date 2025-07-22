# Project Name: Thronestead©
# File Name: admin_events.py
# Version:  7/1/2025 10:38
# Developer: Deathsgift66

"""Admin endpoints for managing global events."""

from datetime import datetime

from fastapi import APIRouter, Depends
from ..rate_limiter import limiter
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session

from services.audit_service import log_action

from ..database import get_db
from ..security import (
    require_user_id,
    verify_api_key,
    verify_admin,
    require_csrf_token,
)

router = APIRouter(prefix="/api/admin/events", tags=["admin_events"])


@router.get("/list", summary="List global events")
@limiter.limit("10/minute")
def list_events(
    verify: str = Depends(verify_api_key),
    admin_user_id: str = Depends(require_user_id),
    db: Session = Depends(get_db),
) -> dict:
    """Return all global events ordered by start time."""
    verify_admin(admin_user_id, db)
    rows = db.execute(
        text(
            """
            SELECT event_id, name, description, start_time, end_time,
                   is_active, impact_type, magnitude
              FROM global_events
             ORDER BY start_time DESC
            """
        )
    ).fetchall()
    events = [
        {
            "event_id": r[0],
            "name": r[1],
            "description": r[2],
            "start_time": r[3],
            "end_time": r[4],
            "is_active": r[5],
            "impact_type": r[6],
            "magnitude": float(r[7]) if r[7] is not None else None,
        }
        for r in rows
    ]
    return {"events": events}


class EventPayload(BaseModel):
    name: str
    description: str | None = None
    start_time: datetime | None = None
    end_time: datetime | None = None
    impact_type: str | None = None
    magnitude: float | None = None


@router.post("/create", summary="Create a global event")
@limiter.limit("5/minute")
def create_event(
    payload: EventPayload,
    verify: str = Depends(verify_api_key),
    admin_user_id: str = Depends(require_user_id),
    csrf: str = Depends(require_csrf_token),
    db: Session = Depends(get_db),
) -> dict:
    """Insert a new global event and audit the action."""
    verify_admin(admin_user_id, db)
    result = db.execute(
        text(
            """
            INSERT INTO global_events
                (name, description, start_time, end_time, impact_type, magnitude)
            VALUES
                (:name, :desc, :start, :end, :impact, :mag)
            RETURNING event_id
            """
        ),
        {
            "name": payload.name,
            "desc": payload.description,
            "start": payload.start_time,
            "end": payload.end_time,
            "impact": payload.impact_type,
            "mag": payload.magnitude,
        },
    ).fetchone()
    db.commit()
    log_action(db, admin_user_id, "create_event", payload.name)
    return {"status": "created", "event_id": result[0]}
