import os
from ..env_utils import get_env_var

from fastapi import APIRouter

router = APIRouter(prefix="/api/public-config", tags=["config"])


@router.get("/")
async def public_config():
    """Expose public Supabase configuration for the frontend."""
    return {
        "SUPABASE_URL": get_env_var("SUPABASE_URL"),
        "SUPABASE_ANON_KEY": get_env_var("SUPABASE_ANON_KEY"),
        "MAINTENANCE_MODE": get_env_var("MAINTENANCE_MODE", default="false").lower() == "true",
    }
