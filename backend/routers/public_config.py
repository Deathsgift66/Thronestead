from fastapi import APIRouter
import os

router = APIRouter(prefix="/api", tags=["config"])

@router.get("/public-config")
async def public_config() -> dict:
    """Expose public configuration values for the frontend."""
    return {
        "SUPABASE_URL": os.getenv("SUPABASE_URL", ""),
        "SUPABASE_ANON_KEY": os.getenv("SUPABASE_ANON_KEY", ""),
    }
