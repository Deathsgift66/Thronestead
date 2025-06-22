# Project Name: Thronestead©
# File Name: tutorial.py
# Version 6.13.2025.19.49
# Developer: Deathsgift66

from fastapi import APIRouter, Depends, HTTPException
from ..security import require_user_id
from ..supabase_client import get_supabase_client

router = APIRouter(prefix="/api/tutorial", tags=["tutorial"])


@router.get("/steps", summary="Get Tutorial Steps", response_model=None)
async def steps(user_id: str = Depends(require_user_id)):
    """
    Fetch ordered tutorial steps from the 'tutorial_steps' table for the authenticated user.
    This ensures only valid players can access in-game tutorials.
    """
    supabase = get_supabase_client()

    # Validate user exists
    try:
        user_check = (
            supabase.table("users")
            .select("user_id")
            .eq("user_id", user_id)
            .single()
            .execute()
        )
        if getattr(user_check, "error", None) or not getattr(user_check, "data", None):
            raise HTTPException(status_code=401, detail="Invalid user")
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Failed to validate user") from exc

    # Fetch tutorial steps in order
    try:
        res = (
            supabase.table("tutorial_steps")
            .select("id,title,description,step_number")
            .order("step_number")
            .execute()
        )
        rows = getattr(res, "data", res) or []
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Failed to load tutorial steps") from exc

    # Return structured tutorial list
    steps = [
        {
            "step_id": r.get("id"),
            "title": r.get("title"),
            "description": r.get("description"),
            "step_number": r.get("step_number"),
        }
        for r in rows
    ]

    return {"steps": steps}
