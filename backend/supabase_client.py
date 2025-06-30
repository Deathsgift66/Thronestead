# Project Name: Thronestead©
# File Name: supabase_client.py
# Version: 6.13.2025.19.49
# Developer: Deathsgift66
"""Supabase client configuration for Thronestead©.

Provides a shared connection instance to Supabase using the anonymous key.
Used for server-side operations including authentication, data writes, and RLS-sensitive queries.
"""

import logging
import os
from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover - type check only
    from supabase import Client

try:  # pragma: no cover - optional dependency
    from supabase import create_client
except ImportError as e:  # pragma: no cover
    raise RuntimeError(
        "❌ Supabase client library not installed. Run `pip install supabase`"
    ) from e

# -------------------------------
# 🔐 Load Supabase Credentials
# -------------------------------
from .env_utils import get_env_var

SUPABASE_URL = get_env_var("SUPABASE_URL")
SUPABASE_KEY = get_env_var("SUPABASE_SERVICE_ROLE_KEY") or get_env_var("SUPABASE_ANON_KEY")

# -------------------------------
# ⚙️ Create Supabase Client
# -------------------------------
supabase: "Client | None" = None

if not SUPABASE_URL or not SUPABASE_KEY:
    logging.error(
        "❌ Missing Supabase credentials. Set SUPABASE_URL and SUPABASE_ANON_KEY"
        " or SUPABASE_SERVICE_ROLE_KEY."
    )
else:
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        logging.info("✅ Supabase client initialized successfully.")
    except Exception:
        logging.exception("❌ Failed to initialize Supabase client.")
        supabase = None


# -------------------------------
# 🧰 Exported Client Accessor
# -------------------------------
def get_supabase_client() -> "Client":
    """Return the initialized Supabase client."""
    if supabase is None:
        raise RuntimeError(
            "Supabase client not initialized. Check SUPABASE_URL and credentials."
        )
    return supabase
