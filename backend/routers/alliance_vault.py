from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/api/alliance-vault", tags=["alliance_vault"])


class VaultAction(BaseModel):
    amount: int


@router.get("/summary")
async def summary():
    return {"summary": {}}


@router.get("/custom-board")
async def custom_board():
    return {"board": []}


@router.post("/deposit")
async def deposit(payload: VaultAction):
    return {"message": "Deposited", "amount": payload.amount}


@router.post("/withdraw")
async def withdraw(payload: VaultAction):
    return {"message": "Withdrawn", "amount": payload.amount}


@router.get("/history")
async def history():
    return {"history": []}

