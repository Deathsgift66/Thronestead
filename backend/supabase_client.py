# Project Name: Thronestead©
# File Name: supabase_client.py
# Version:  7/1/2025 10:38
# Developer: Deathsgift66
"""Supabase client configuration for Thronestead©.

Provides a shared connection instance to Supabase using the anonymous key.
Used for server-side operations including authentication, data writes, and RLS-sensitive queries.
"""

import logging
from functools import lru_cache
from typing import TYPE_CHECKING
import inspect
import asyncio

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

@lru_cache(maxsize=1)
def get_supabase_client() -> "Client":
    """Return a lazily initialized Supabase client."""
    url = get_env_var("SUPABASE_URL")
    key = get_env_var("SUPABASE_SERVICE_ROLE_KEY") or get_env_var("SUPABASE_ANON_KEY")

    if not url or not key:
        raise RuntimeError(
            "Missing Supabase credentials. Set SUPABASE_URL and SUPABASE_ANON_KEY "
            "or SUPABASE_SERVICE_ROLE_KEY."
        )

    try:
        return create_client(url, key)
    except Exception as exc:
        logging.exception("❌ Failed to initialize Supabase client.")
        raise RuntimeError("Supabase client initialization failed") from exc


def maybe_await(obj):
    """Return awaited result if ``obj`` is awaitable."""
    if inspect.isawaitable(obj):
        return asyncio.run(obj)
    return obj
