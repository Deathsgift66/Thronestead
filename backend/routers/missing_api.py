"""Placeholder routes for pending API endpoints."""

from typing import Any, List

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from ..security import verify_jwt_token

router = APIRouter(prefix="/api", tags=["placeholders"])


class BattleDeclarePayload(BaseModel):
    target_id: str


@router.post("/battle/declare")
def declare_battle(
    payload: BattleDeclarePayload,
    user_id: str = Depends(verify_jwt_token),
) -> dict:
    return {"status": "pending", "target": payload.target_id}


class AccountUpdatePayload(BaseModel):
    field: str
    value: Any


@router.post("/account/update")
def update_account(
    payload: AccountUpdatePayload,
    user_id: str = Depends(verify_jwt_token),
) -> dict:
    return {"status": "updated"}


class AdminEventPayload(BaseModel):
    name: str


@router.post("/admin/events/create")
def create_event(
    payload: AdminEventPayload,
    user_id: str = Depends(verify_jwt_token),
) -> dict:
    return {"status": "created"}


class AdminFieldPayload(BaseModel):
    kingdom_id: int
    field: str
    value: Any


@router.post("/admin/kingdom/update_field")
def update_kingdom_field(
    payload: AdminFieldPayload,
    user_id: str = Depends(verify_jwt_token),
) -> dict:
    return {"status": "updated"}


class RollbackPayload(BaseModel):
    password: str


@router.post("/admin/system/rollback")
def system_rollback(
    payload: RollbackPayload,
    user_id: str = Depends(verify_jwt_token),
) -> dict:
    return {"status": "queued"}


@router.get("/alliance-vault/custom-board")
def alliance_vault_board() -> dict:
    return {"board": []}


@router.get("/alliance/custom/vault")
def alliance_custom_vault() -> dict:
    return {"vault": []}


class TreatyProposal(BaseModel):
    partner_alliance_id: int
    treaty_type: str


@router.post("/alliance/treaties/propose")
def propose_treaty(
    payload: TreatyProposal,
    user_id: str = Depends(verify_jwt_token),
) -> dict:
    return {"status": "proposed"}


@router.get("/battle/history")
def battle_history() -> dict:
    return {"history": []}


class BattleOrdersPayload(BaseModel):
    war_id: int
    orders: List[Any]


@router.post("/battle/orders")
def battle_orders(
    payload: BattleOrdersPayload,
    user_id: str = Depends(verify_jwt_token),
) -> dict:
    return {"status": "received"}


@router.get("/battle/wars")
def battle_wars() -> dict:
    return {"wars": []}


@router.get("/black_market/listings")
def black_market_listings() -> dict:
    return {"listings": []}


class PurchasePayload(BaseModel):
    listing_id: int
    quantity: int


@router.post("/black_market/purchase")
def black_market_purchase(
    payload: PurchasePayload,
    user_id: str = Depends(verify_jwt_token),
) -> dict:
    return {"status": "purchased"}


@router.get("/conflicts/all")
def conflicts_all() -> dict:
    return {"conflicts": []}


@router.get("/kingdom_troops/unlocked")
def kingdom_troops_unlocked() -> dict:
    return {"troops": []}


@router.post("/progression/castle/upgrade")
def castle_upgrade(
    user_id: str = Depends(verify_jwt_token),
) -> dict:
    return {"status": "queued"}


class KnightName(BaseModel):
    name: str


@router.post("/progression/knights/promote")
def promote_knight(
    payload: KnightName,
    user_id: str = Depends(verify_jwt_token),
) -> dict:
    return {"status": "promoted"}


@router.put("/progression/knights/rename")
def rename_knight(
    payload: KnightName,
    user_id: str = Depends(verify_jwt_token),
) -> dict:
    return {"status": "renamed"}


@router.put("/progression/nobles/rename")
def rename_noble(
    payload: KnightName,
    user_id: str = Depends(verify_jwt_token),
) -> dict:
    return {"status": "renamed"}

