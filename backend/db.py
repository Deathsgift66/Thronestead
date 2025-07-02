# Project Name: Thronestead©
# File Name: db.py
# Version:  7/1/2025 10:38
# Developer: Deathsgift66
"""Legacy database helpers used by parts of the backend."""

from __future__ import annotations

import logging
from typing import Any, Sequence

import psycopg2
from psycopg2.extras import RealDictCursor

from .env_utils import get_env_var

logger = logging.getLogger("Thronestead.LegacyDB")

DATABASE_URL = get_env_var(
    "DATABASE_URL",
    default=get_env_var(
        "SUPABASE_DB_URL", "postgresql://postgres:postgres@localhost/postgres"
    ),
)


def _connect():
    """Return a new psycopg2 connection."""
    return psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)


def query(sql: str, params: Sequence[Any] | None = None) -> list[dict[str, Any]]:
    """Execute ``sql`` and return all rows as dicts."""
    with _connect() as conn, conn.cursor() as cur:
        cur.execute(sql, params)
        return cur.fetchall()


def execute(sql: str, params: Sequence[Any] | None = None) -> list[dict[str, Any]]:
    """Execute ``sql`` and commit the transaction."""
    with _connect() as conn, conn.cursor() as cur:
        cur.execute(sql, params)
        conn.commit()
        return cur.fetchall() if cur.description else []


class _DB:
    def query(
        self, sql: str, params: Sequence[Any] | None = None
    ) -> list[dict[str, Any]]:
        return query(sql, params)

    def execute(
        self, sql: str, params: Sequence[Any] | None = None
    ) -> list[dict[str, Any]]:
        return execute(sql, params)


db = _DB()

__all__ = ["db", "query", "execute"]
