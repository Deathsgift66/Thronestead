# Project Name: Thronestead©
# File Name: alliance_members_view.py
# Version: 6.14.2025
# Developer: Deathsgift66

"""
Project: Thronestead ©
File: alliance_members_view.py
Role: API routes for alliance members view.
Version: 2025-06-21
"""

from fastapi import APIRouter, Depends, HTTPException
from ..security import require_user_id
from ..supabase_client import get_supabase_client

router = APIRouter(prefix="/api/alliance-members", tags=["alliance_members_view"])


@router.get("/view", response_model=None)
def view_alliance_members(user_id: str = Depends(require_user_id)):
    """
    Returns detailed information about all members in the same alliance
    as the authenticated user using the Supabase RPC view.
    """
    supabase = get_supabase_client()

    # ✅ Fetch alliance_id for the current user to ensure access
    user_res = (
        supabase.table("users")
        .select("alliance_id")
        .eq("user_id", user_id)
        .single()
        .execute()
    )

    if getattr(user_res, "error", None):
        raise HTTPException(status_code=500, detail="Failed to verify user alliance")
    if not user_res.data or not user_res.data.get("alliance_id"):
        raise HTTPException(status_code=403, detail="You are not in an alliance")

    # 🚀 Call Supabase RPC to get enriched member data
    members_res = (
        supabase.rpc("get_alliance_members_detailed", {"viewer_user_id": user_id})
        .execute()
    )
    if getattr(members_res, "error", None):
        raise HTTPException(status_code=500, detail="RPC failed: could not fetch members")

    members = getattr(members_res, "data", members_res)
    return {"alliance_members": members}
