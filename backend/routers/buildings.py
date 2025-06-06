from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/api/buildings", tags=["buildings"])


class UpgradePayload(BaseModel):
    building: str


@router.post("/upgrade")
async def upgrade(payload: UpgradePayload):
    return {"message": "upgrading", "building": payload.building}

