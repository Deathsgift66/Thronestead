from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/api/alliance_members", tags=["alliance_members"])


class MemberAction(BaseModel):
    user_id: str


@router.get("")
async def list_members():
    return {"members": []}


@router.post("/promote")
async def promote(payload: MemberAction):
    return {"message": "Promoted", "user_id": payload.user_id}


@router.post("/demote")
async def demote(payload: MemberAction):
    return {"message": "Demoted", "user_id": payload.user_id}


@router.post("/remove")
async def remove(payload: MemberAction):
    return {"message": "Removed", "user_id": payload.user_id}

