import os

from ..env_utils import get_env

from fastapi import APIRouter

router = APIRouter(prefix="/api/public-config", tags=["config"])


@router.get("/")
async def public_config():
    """Expose public Supabase configuration for the frontend."""
    return {
        "SUPABASE_URL": get_env("SUPABASE_URL", "VITE_PUBLIC_SUPABASE_URL"),
        "SUPABASE_ANON_KEY": get_env(
            "SUPABASE_ANON_KEY",
            "SUPABASE_SERVICE_ROLE_KEY",
            "VITE_PUBLIC_SUPABASE_ANON_KEY",
        ),
        "MAINTENANCE_MODE": get_env("MAINTENANCE_MODE", default="false").lower() == "true",
    }
