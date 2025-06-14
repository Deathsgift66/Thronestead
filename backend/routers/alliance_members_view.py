# Project Name: Kingmakers Rise©
# File Name: alliance_members_view.py
# Version: 6.13.2025.19.49
# Developer: Deathsgift66

from fastapi import APIRouter, Depends, HTTPException
from ..security import require_user_id
from ..supabase_client import get_supabase_client

router = APIRouter(prefix="/api/alliance-members", tags=["alliance_members_view"])


@router.get("/view")
def view_alliance_members(user_id: str = Depends(require_user_id)):
    """
    Returns detailed information about all members in the same alliance
    as the authenticated user using the Supabase RPC view.
    """
    supabase = get_supabase_client()

    # Fetch the requesting user's alliance_id
    user_res = (
        supabase.table("users")
        .select("alliance_id")
        .eq("user_id", user_id)
        .single()
        .execute()
    )
    if getattr(user_res, "error", None) or not getattr(user_res, "data", None):
        raise HTTPException(status_code=401, detail="Not authorized")

    # Retrieve detailed alliance members via stored procedure
    members_res = (
        supabase.rpc("get_alliance_members_detailed", {"viewer_user_id": user_id})
        .execute()
    )
    if getattr(members_res, "error", None):
        raise HTTPException(status_code=500, detail="Failed to retrieve alliance members")

    members = getattr(members_res, "data", members_res)
    return {"alliance_members": members}
