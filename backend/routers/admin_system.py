# Project Name: Thronestead©
# File Name: admin_system.py
# Version:  7/1/2025 10:38
# Developer: Deathsgift66
"""Admin endpoints for critical system operations."""

from fastapi import APIRouter, Depends, HTTPException
from collections import defaultdict
import time
from ..env_utils import get_env_var
from pydantic import BaseModel
from sqlalchemy.orm import Session

from services.audit_service import log_action

from ..database import get_db
from ..security import require_user_id, verify_api_key, require_csrf_token

router = APIRouter(prefix="/api/admin/system", tags=["admin_system"])

ROLLBACK_ATTEMPTS: dict[str, list[float]] = defaultdict(list)
ROLLBACK_WINDOW = 300  # 5 minutes
MAX_ATTEMPTS = 3


class RollbackPayload(BaseModel):
    """Password required to trigger a system rollback."""

    password: str


@router.post("/rollback")
def rollback_system(
    payload: RollbackPayload,
    verify: str = Depends(verify_api_key),
    admin_user_id: str = Depends(require_user_id),
    csrf: str = Depends(require_csrf_token),
    db: Session = Depends(get_db),
) -> dict:
    """Trigger a database rollback if the master password matches."""
    now = time.time()
    attempts = [t for t in ROLLBACK_ATTEMPTS[admin_user_id] if now - t < ROLLBACK_WINDOW]
    ROLLBACK_ATTEMPTS[admin_user_id] = attempts
    if len(attempts) >= MAX_ATTEMPTS:
        raise HTTPException(status_code=429, detail="Too many rollback attempts")
    master = get_env_var("MASTER_ROLLBACK_PASSWORD")
    if not master or payload.password != master:
        attempts.append(now)
        ROLLBACK_ATTEMPTS[admin_user_id] = attempts
        raise HTTPException(status_code=403, detail="Invalid master password")

    ROLLBACK_ATTEMPTS[admin_user_id] = []

    log_action(db, admin_user_id, "Rollback System", "Admin triggered rollback")
    return {"status": "rollback_triggered"}
