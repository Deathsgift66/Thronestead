"""Current user utilities."""

from fastapi import APIRouter, Depends

from ..security import get_current_user

router = APIRouter(prefix="/api", tags=["auth"])


@router.get("/me")
async def get_me(user: dict = Depends(get_current_user)):
    """Return the currently authenticated user."""
    return user

