from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/api/wars", tags=["wars"])


class DeclarePayload(BaseModel):
    target: str


@router.post("/declare")
async def declare_war(payload: DeclarePayload):
    return {"message": "War declared", "target": payload.target}

