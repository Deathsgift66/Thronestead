# Project Name: Kingmakers Rise©
# File Name: __init__.py
# Version: 6.13.2025.19.49
# Developer: Deathsgift66

"""
This __init__.py initializes the core backend package for Kingmakers Rise©.
It sets up environment access, logging, Supabase integration, and utility loading.
This file assumes FastAPI app structure, Supabase SDK, and environment-based configuration.
"""

import os
import logging

try:
    from dotenv import load_dotenv
except Exception:  # pragma: no cover - optional in some environments
    load_dotenv = lambda *_, **__: None  # type: ignore

try:
    from supabase import create_client, Client
except Exception:  # pragma: no cover - optional in tests
    create_client = None  # type: ignore
    Client = None  # type: ignore

# Load .ENV variables (Render environment uses system variables by default)
load_dotenv(".ENV")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("KingmakersRise")

# Supabase configuration from environment variables
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")  # Use service role key for backend tasks

supabase = None
if create_client and SUPABASE_URL and SUPABASE_KEY:
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception as exc:  # pragma: no cover - network/dependency issues
        logger.exception("Failed to initialize Supabase client")
        supabase = None
else:
    logger.warning(
        "Supabase credentials missing or client library unavailable; continuing without Supabase"
    )

if supabase:
    logger.info("Supabase client initialized")

# Exported objects from module
__all__ = ["supabase", "logger"]
