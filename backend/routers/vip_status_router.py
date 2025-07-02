# Project Name: Thronestead©
# File Name: vip_status_router.py
# Version:  7/1/2025 10:38
# Developer: Deathsgift66

"""
Project: Thronestead ©
File: vip_status_router.py
Role: API routes for vip status router.
Version: 2025-06-21
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from services.vip_status_service import get_vip_status

from ..database import get_db
from ..security import require_user_id

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



# Map legacy endpoint to ``vip_status`` to avoid duplicate logic
alt_router.add_api_route(
    "/api/user/vip",
    vip_status,
    methods=["GET"],
    summary="Legacy VIP status endpoint",
)
