# Project Name: Thronestead©
# File Name: message_service.py
# Version: 6.13.2025.19.49
# Developer: Deathsgift66
"""Utility functions for player messaging."""

from __future__ import annotations

from typing import Any

import logging

try:  # pragma: no cover - optional dependency
    from supabase import Client
except ImportError:  # pragma: no cover
    Client = Any  # type: ignore

logger = logging.getLogger(__name__)


def count_unread_messages(supabase: Client, user_id: str) -> int:
    """Return the number of unread messages for ``user_id``.

    Args:
        supabase: Initialized Supabase client.
        user_id: Target recipient user ID.

    Returns:
        int: Count of unread messages.
    """
    try:
        result = (
            supabase.table("player_messages")
            .select("message_id")
            .eq("recipient_id", user_id)
            .eq("is_read", False)
            .execute()
        )
        data = getattr(result, "data", None)
        if data is None and isinstance(result, dict):
            data = result.get("data")
        return len(data or [])
    except Exception as exc:  # pragma: no cover - network errors
        logger.warning("Failed to fetch unread count: %s", exc)
        return 0
