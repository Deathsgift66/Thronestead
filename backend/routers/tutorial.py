from fastapi import APIRouter, Depends, HTTPException

from ..security import require_user_id


from ..supabase_client import get_supabase_client


router = APIRouter(prefix="/api/tutorial", tags=["tutorial"])


@router.get("/steps")
async def steps(user_id: str = Depends(require_user_id)):
    """Return ordered tutorial steps from Supabase for the authenticated user."""
    supabase = get_supabase_client()

    user_check = (
        supabase.table("users").select("user_id").eq("user_id", user_id).single().execute()
    )
    if getattr(user_check, "error", None) or not getattr(user_check, "data", None):
        raise HTTPException(status_code=401, detail="Invalid user")

    res = (
        supabase.table("tutorial_steps")
        .select("id,title,description,step_number")
        .order("step_number")
        .execute()
    )
    rows = getattr(res, "data", res) or []
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
