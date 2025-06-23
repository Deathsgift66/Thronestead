from fastapi import APIRouter
import os

router = APIRouter(prefix="/api/public-config", tags=["config"])

@router.get("/")
async def public_config():
    """Expose public Supabase configuration for the frontend."""
    return {
        "SUPABASE_URL": os.getenv("SUPABASE_URL"),
        "SUPABASE_ANON_KEY": os.getenv("SUPABASE_ANON_KEY"),
    }
