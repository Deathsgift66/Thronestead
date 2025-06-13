# Project Name: Kingmakers Rise©
# File Name: policies_laws.py
# Version 6.13.2025.19.49
# Developer: Deathsgift66
"""
FastAPI routes for policies and laws management.
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from ..security import verify_jwt_token


from ..supabase_client import get_supabase_client


router = APIRouter(prefix="/api/policies-laws", tags=["policies-laws"])


class UpdatePolicyPayload(BaseModel):
    policy_id: int


class UpdateLawsPayload(BaseModel):
    law_ids: list[int]


@router.get("/catalogue")
def catalogue(user_id: str = Depends(verify_jwt_token)):
    """Return active policy and law entries."""
    supabase = get_supabase_client()
    try:
        result = (
            supabase.table("policies_laws_catalogue")
            .select("*")
            .eq("is_active", True)
            .order("unlock_at_level")
            .execute()
        )
    except Exception as exc:  # pragma: no cover - network/db errors
        raise HTTPException(status_code=500, detail="Failed to fetch catalogue") from exc
    entries = getattr(result, "data", result) or []
    return {"entries": entries}


@router.get("/user")
def user_settings(user_id: str = Depends(verify_jwt_token)):
    """Return the user's current policy and laws."""
    supabase = get_supabase_client()
    try:
        result = (
            supabase.table("users")
            .select("active_policy,active_laws")
            .eq("user_id", user_id)
            .single()
            .execute()
        )
    except Exception as exc:  # pragma: no cover - network/db errors
        raise HTTPException(status_code=500, detail="Failed to fetch user data") from exc
    data = getattr(result, "data", result) or {}
    return {
        "active_policy": data.get("active_policy"),
        "active_laws": data.get("active_laws") or [],
    }


@router.post("/policy")
def update_policy(payload: UpdatePolicyPayload, user_id: str = Depends(verify_jwt_token)):
    """Update the user's selected policy."""
    supabase = get_supabase_client()
    try:
        supabase.table("users").update({"active_policy": payload.policy_id}).eq("user_id", user_id).execute()
    except Exception as exc:  # pragma: no cover - network/db errors
        raise HTTPException(status_code=500, detail="Failed to update policy") from exc
    return {"message": "ok"}


@router.post("/laws")
def update_laws(payload: UpdateLawsPayload, user_id: str = Depends(verify_jwt_token)):
    """Update the user's active laws."""
    supabase = get_supabase_client()
    try:
        supabase.table("users").update({"active_laws": payload.law_ids}).eq("user_id", user_id).execute()
    except Exception as exc:  # pragma: no cover - network/db errors
        raise HTTPException(status_code=500, detail="Failed to update laws") from exc
    return {"message": "ok"}
