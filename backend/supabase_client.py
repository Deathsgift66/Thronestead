# Project Name: Thronestead©
# File Name: supabase_client.py
# Version: 6.13.2025.19.49
# Developer: Deathsgift66

"""
Supabase client configuration for Thronestead©.

Provides a shared connection instance to Supabase using the service role key.
Used for server-side operations including authentication, data writes, and RLS-sensitive queries.
"""

import os
import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from supabase import Client  # for type hints only

try:  # pragma: no cover - optional dependency
    from supabase import create_client
except ImportError as e:  # pragma: no cover
    raise RuntimeError("❌ Supabase client library not installed. Run `pip install supabase`") from e

# -------------------------------
# 🔐 Load Supabase Credentials
# -------------------------------
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")

# -------------------------------
# ⚙️ Create Supabase Client
# -------------------------------
supabase: "Client | None" = None

if not SUPABASE_URL:
    logging.error("❌ Missing Supabase URL")
else:
    key = SUPABASE_SERVICE_ROLE_KEY or SUPABASE_ANON_KEY
    if not key:
        logging.error(
            "❌ Missing Supabase credentials: SUPABASE_SERVICE_ROLE_KEY or SUPABASE_ANON_KEY not set."
        )
    else:
        try:
            supabase = create_client(SUPABASE_URL, key)
            logging.info("✅ Supabase client initialized successfully.")
        except Exception:
            logging.exception("❌ Failed to initialize Supabase client.")
            supabase = None

# -------------------------------
# 🧰 Exported Client Accessor
# -------------------------------
def get_supabase_client() -> "Client":
    """
    Returns:
        Supabase Client instance

    Raises:
        RuntimeError: if the client failed to initialize
    """
    if supabase is None:
        raise RuntimeError(
            "Supabase client not initialized. Check SUPABASE_URL and credentials."
        )
    return supabase
