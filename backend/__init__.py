# Project Name: Thronestead©
# File Name: __init__.py
# Version:  7/1/2025 10:38
# Developer: Deathsgift66

"""
This __init__.py initializes the core backend package for Thronestead©.
It sets up environment access, logging, Supabase integration, and utility loading.
This file assumes FastAPI app structure, Supabase SDK, and environment-based configuration.
"""

import logging



# The backend has a dedicated ``supabase_client`` module that creates and
# exposes the connection instance.  Importing it here ensures a single
# initialization point and avoids duplicate log messages during startup.
try:
    from .supabase_client import get_supabase_client
except Exception:  # pragma: no cover - optional dependency
    get_supabase_client = None  # type: ignore[misc]

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("Thronestead")

# Initialise the Supabase client via ``backend.supabase_client`` if available.
supabase = None
if get_supabase_client:
    try:
        supabase = get_supabase_client()
    except Exception:  # pragma: no cover - let caller handle missing client
        logger.exception("Failed to initialize Supabase client")
        supabase = None

# Exported objects from module
__all__ = ["supabase", "logger"]
