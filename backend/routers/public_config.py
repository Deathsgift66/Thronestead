# Project Name: Thronestead©
# File Name: public_config.py
# Version 6.13.2025.19.49
# Developer: Deathsgift66

"""
Project: Thronestead ©
File: public_config.py
Role: API routes for public config.
Version: 2025-06-21
"""

from fastapi import APIRouter
import os

# Initialize the FastAPI router with tag for documentation and grouping
router = APIRouter(prefix="/api", tags=["config"])


@router.get("/public-config")
async def public_config() -> dict:
    """
    Public configuration endpoint exposed to the frontend.
    Only returns non-sensitive keys such as Supabase anonymous access credentials.
    """
    return {
        # Supabase base URL for client SDK initialization
        "SUPABASE_URL": os.getenv("SUPABASE_URL", ""),

        # Anonymous key used by frontend clients to interact with Supabase public tables/functions
        "SUPABASE_ANON_KEY": os.getenv("SUPABASE_ANON_KEY", ""),
    }
