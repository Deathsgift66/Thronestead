from fastapi import APIRouter, Depends
from .progression_router import get_user_id
from ..data import vip_levels

router = APIRouter(prefix="/api/kingdom", tags=["vip"])

@router.get("/vip_status")
async def vip_status(user_id: str = Depends(get_user_id)):
    level = vip_levels.get(user_id, 0)
    return {"vip_level": level}

