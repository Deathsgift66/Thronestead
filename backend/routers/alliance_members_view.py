from fastapi import APIRouter, Depends, HTTPException, Header

router = APIRouter()


def get_current_user_id(x_user_id: str | None = Header(None)) -> str:
    if not x_user_id:
        raise HTTPException(status_code=401, detail="User ID header missing")
    return x_user_id


from ..supabase_client import get_supabase_client


@router.get("/api/alliance-members/view")
def view_alliance_members(user_id: str = Depends(get_current_user_id)):
    supabase = get_supabase_client()

    user_res = (
        supabase.table("users")
        .select("alliance_id")
        .eq("user_id", user_id)
        .single()
        .execute()
    )
    user = getattr(user_res, "data", user_res)
    if not user:
        raise HTTPException(401, "Not authorized")

    members_res = (
        supabase.rpc("get_alliance_members_detailed", {"viewer_user_id": user_id})
        .execute()
    )
    members = getattr(members_res, "data", members_res)

    return {"alliance_members": members}
