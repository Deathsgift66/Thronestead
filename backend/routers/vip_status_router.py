# Project Name: Kingmakers Rise©
# File Name: vip_status_router.py
# Version 6.13.2025.19.49
# Developer: Deathsgift66
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..database import get_db
from ..security import require_user_id
from services.vip_status_service import get_vip_status

router = APIRouter(prefix="/api/kingdom", tags=["vip"])

@router.get("/vip_status")
def vip_status(
    user_id: str = Depends(require_user_id),
    db: Session = Depends(get_db),
):
    record = get_vip_status(db, user_id)
    if not record:
        return {"vip_level": 0, "expires_at": None, "founder": False}
    return record

