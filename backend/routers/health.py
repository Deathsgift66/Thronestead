# Project Name: Thronestead©
# File Name: health.py
# Version:  7/1/2025 10:38
# Developer: Deathsgift66

"""
Project: Thronestead ©
File: health.py
Role: API routes for health.
Version: 2025-06-21
"""

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from ..database import get_db

router = APIRouter(prefix="/api/health", tags=["health"])


@router.get("/", summary="Health Check", description="Basic API health check.")
def health_check() -> dict[str, str]:
    """Return basic heartbeat status for uptime monitors."""
    return {"status": "ok"}


@router.get("/db", summary="Database Health", description="Checks DB connection.")
def database_health(db: Session = Depends(get_db)) -> dict[str, bool | str]:
    """Return database connectivity status."""
    try:
        db.execute(text("SELECT 1"))
        return {"status": "ok", "db": True}
    except Exception:
        return {"status": "error", "db": False}
