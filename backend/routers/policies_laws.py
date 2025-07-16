# Project Name: Thronestead©
# File Name: policies_laws.py
# Version: 7/1/2025 10:38
# Developer: Deathsgift66
"""API routes for user policy and law management."""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..security import verify_jwt_token
from ..supabase_client import get_supabase_client
from ..database import get_db
from services.audit_service import log_action

router = APIRouter(prefix="/api/policies-laws", tags=["policies-laws"])


class UpdatePolicyPayload(BaseModel):
    policy_id: int


class UpdateLawsPayload(BaseModel):
    law_ids: list[int]


@router.get("/catalogue")
def catalogue(user_id: str = Depends(verify_jwt_token)):
    """Return all policies and laws sorted by id."""
    supabase = get_supabase_client()
    try:
        result = (
            supabase.table("policies_laws_catalogue").select("*").order("id").execute()
        )
    except Exception as exc:  # pragma: no cover - network failure
        raise HTTPException(500, f"Failed to fetch catalogue: {exc}") from exc

    entries = getattr(result, "data", result) or []
    return {"entries": entries}


@router.get("/user")
def user_settings(user_id: str = Depends(verify_jwt_token)):
    """Return the caller's active policy and law ids."""
    supabase = get_supabase_client()
    try:
        result = (
            supabase.table("users")
            .select("active_policy,active_laws")
            .eq("user_id", user_id)
            .single()
            .execute()
        )
    except Exception as exc:  # pragma: no cover - network failure
        raise HTTPException(500, f"Failed to fetch user data: {exc}") from exc

    data = getattr(result, "data", result) or {}
    return {
        "active_policy": data.get("active_policy"),
        "active_laws": data.get("active_laws") or [],
    }


def _validate_policy_id(policy_id: int, supabase) -> None:
    res = (
        supabase.table("policies_laws_catalogue")
        .select("id")
        .eq("id", policy_id)
        .eq("type", "policy")
        .single()
        .execute()
    )
    if not getattr(res, "data", res):
        raise HTTPException(400, "Invalid policy id")


def _validate_law_ids(law_ids: list[int], supabase) -> None:
    for lid in law_ids:
        res = (
            supabase.table("policies_laws_catalogue")
            .select("id")
            .eq("id", lid)
            .eq("type", "law")
            .single()
            .execute()
        )
        if not getattr(res, "data", res):
            raise HTTPException(400, f"Invalid law id {lid}")


MAX_ACTIVE_LAWS = 5


@router.post("/policy")
def update_policy(
    payload: UpdatePolicyPayload,
    user_id: str = Depends(verify_jwt_token),
    db: Session = Depends(get_db),
):
    """Set the active policy for the user."""
    supabase = get_supabase_client()
    _validate_policy_id(payload.policy_id, supabase)
    try:
        supabase.table("users").update({"active_policy": payload.policy_id}).eq(
            "user_id", user_id
        ).execute()
    except Exception as exc:
        raise HTTPException(500, f"Failed to update policy: {exc}") from exc

    log_action(db, user_id, "policy_update", str(payload.policy_id))
    settings = user_settings(user_id)
    return {"message": "Policy updated", **settings}


@router.post("/laws")
def update_laws(
    payload: UpdateLawsPayload,
    user_id: str = Depends(verify_jwt_token),
    db: Session = Depends(get_db),
):
    """Replace the user's active laws."""
    if len(payload.law_ids) > MAX_ACTIVE_LAWS:
        raise HTTPException(400, f"Too many active laws (max {MAX_ACTIVE_LAWS})")

    supabase = get_supabase_client()
    _validate_law_ids(payload.law_ids, supabase)
    try:
        supabase.table("users").update({"active_laws": payload.law_ids}).eq(
            "user_id", user_id
        ).execute()
    except Exception as exc:
        raise HTTPException(500, f"Failed to update laws: {exc}") from exc

    log_action(db, user_id, "laws_update", ",".join(map(str, payload.law_ids)))
    settings = user_settings(user_id)
    return {"message": "Laws updated", **settings}
