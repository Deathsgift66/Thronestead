# Project Name: Kingmakers Rise©
# File Name: supabase_client.py
# Version 6.13.2025.19.49
# Developer: Deathsgift66
"""Supabase client configuration for the API."""

import logging
import os


try:  # pragma: no cover - optional dependency
    from supabase import create_client
except ImportError as e:  # pragma: no cover - library missing
    raise RuntimeError("supabase client library not installed") from e


SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
    logging.error("Supabase credentials missing; set SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY")
    supabase = None
else:
    supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)


def get_supabase_client() -> "create_client":
    """Return the configured Supabase client or raise if unavailable."""

    if supabase is None:
        raise RuntimeError("Supabase credentials not configured")
    return supabase

