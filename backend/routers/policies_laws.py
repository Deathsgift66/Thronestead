# Project Name: Kingmakers Rise©
# File Name: policies_laws.py
# Version: 6.13.2025.19.49
# Developer: Deathsgift66

"""
FastAPI router for managing user policies and laws settings.
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from ..security import verify_jwt_token
from ..supabase_client import get_supabase_client

router = APIRouter(prefix="/api/policies-laws", tags=["policies-laws"])


# -------------------------------
# Payload Models
# -------------------------------

class UpdatePolicyPayload(BaseModel):
    policy_id: int


class UpdateLawsPayload(BaseModel):
    law_ids: list[int]


# -------------------------------
# Endpoint: Get Catalogue of Active Policies/Laws
# -------------------------------
@router.get("/catalogue")
def get_catalogue(user_id: str = Depends(verify_jwt_token)):
    """
    Return all active policies and laws in the catalogue sorted by unlock level.
    """
    supabase = get_supabase_client()
    try:
        result = (
            supabase.table("policies_laws_catalogue")
            .select("*")
            .eq("is_active", True)
            .order("unlock_at_level")
            .execute()
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Failed to fetch catalogue") from exc

    entries = getattr(result, "data", result) or []
    return {"entries": entries}


# -------------------------------
# Endpoint: Get User's Current Settings
# -------------------------------
@router.get("/user")
def get_user_policies(user_id: str = Depends(verify_jwt_token)):
    """
    Return the current policy and active laws for the authenticated user.
    """
    supabase = get_supabase_client()
    try:
        result = (
            supabase.table("users")
            .select("active_policy,active_laws")
            .eq("user_id", user_id)
            .single()
            .execute()
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Failed to fetch user data") from exc

    data = getattr(result, "data", result) or {}
    return {
        "active_policy": data.get("active_policy"),
        "active_laws": data.get("active_laws") or [],
    }


# -------------------------------
# Endpoint: Update User Policy
# -------------------------------
@router.post("/policy")
def update_user_policy(
    payload: UpdatePolicyPayload,
    user_id: str = Depends(verify_jwt_token),
):
    """
    Set the currently active policy for a user.
    """
    supabase = get_supabase_client()
    try:
        supabase.table("users") \
            .update({"active_policy": payload.policy_id}) \
            .eq("user_id", user_id) \
            .execute()
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Failed to update policy") from exc

    return {"message": "Policy updated", "policy_id": payload.policy_id}


# -------------------------------
# Endpoint: Update User Laws
# -------------------------------
@router.post("/laws")
def update_user_laws(
    payload: UpdateLawsPayload,
    user_id: str = Depends(verify_jwt_token),
):
    """
    Update the set of active laws a user is currently using.
    """
    supabase = get_supabase_client()
    try:
        supabase.table("users") \
            .update({"active_laws": payload.law_ids}) \
            .eq("user_id", user_id) \
            .execute()
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Failed to update laws") from exc

    return {"message": "Laws updated", "law_ids": payload.law_ids}
