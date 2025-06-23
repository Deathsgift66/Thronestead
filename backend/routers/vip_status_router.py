# Project Name: Thronestead©
# File Name: vip_status_router.py
# Version 6.13.2025.19.49
# Developer: Deathsgift66

"""
Project: Thronestead ©
File: vip_status_router.py
Role: API routes for vip status router.
Version: 2025-06-21
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..database import get_db
from ..security import require_user_id
from ..db import db
from services.vip_status_service import get_vip_status

# Define the API router with kingdom-scoped prefix
router = APIRouter(prefix="/api/kingdom", tags=["vip"])
alt_router = APIRouter(tags=["vip"])

@router.get("/vip_status")
def vip_status(
    user_id: str = Depends(require_user_id),
    db: Session = Depends(get_db),
):
    """
    Return the VIP status for the authenticated user.
    Includes: VIP level, expiration date, and founder status.
    """
    record = get_vip_status(db, user_id)
    if not record:
        # Default fallback for non-VIP users
        return {
            "vip_level": 0,
            "expires_at": None,
            "founder": False,
        }

    # Ensure full structure is always returned
    return {
        "vip_level": record.get("vip_level", 0),
        "expires_at": record.get("expires_at"),
        "founder": record.get("founder", False),
    }


@alt_router.get("/api/user/vip")
async def get_vip_status_alt(user_id: str = Depends(require_user_id)):
    """Return VIP status for the authenticated user."""
    rows = db.query(
        "SELECT * FROM kingdom_vip_status WHERE user_id = :uid",
        {"uid": str(user_id)},
    )
    record = rows[0] if rows else None
    if not record:
        return {"vip_level": 0, "founder": False}
    return record
