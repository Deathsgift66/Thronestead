"""Current user utilities."""

from fastapi import APIRouter, Depends

from ..security import get_current_user

router = APIRouter(prefix="/api", tags=["auth"])


@router.get("/me")
async def get_me(user: dict = Depends(get_current_user)):
    """Return key details about the authenticated user."""
    return {
        "kingdom_id": user.get("kingdom_id"),
        "username": user.get("username"),
        "setup_complete": user.get("setup_complete"),
    }

