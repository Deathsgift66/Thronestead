# Comment
# Project Name: Thronestead©
# File Name: admin_system.py
# Version: 7/1/2025 10:31
# Developer: Deathsgift66
"""Admin endpoints for critical system operations."""

from fastapi import APIRouter, Depends, HTTPException
from ..env_utils import get_env_var
from pydantic import BaseModel
from sqlalchemy.orm import Session

from services.audit_service import log_action

from ..database import get_db
from ..security import require_user_id, verify_api_key

router = APIRouter(prefix="/api/admin/system", tags=["admin_system"])


class RollbackPayload(BaseModel):
    """Password required to trigger a system rollback."""

    password: str


@router.post("/rollback")
def rollback_system(
    payload: RollbackPayload,
    verify: str = Depends(verify_api_key),
    admin_user_id: str = Depends(require_user_id),
    db: Session = Depends(get_db),
) -> dict:
    """Trigger a database rollback if the master password matches."""
    master = get_env_var("MASTER_ROLLBACK_PASSWORD")
    if not master or payload.password != master:
        raise HTTPException(status_code=403, detail="Invalid master password")

    log_action(db, admin_user_id, "Rollback System", "Admin triggered rollback")
    return {"status": "rollback_triggered"}
