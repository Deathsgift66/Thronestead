# Project Name: Thronestead©
# File Name: db.py
# Version: 6.14.2025.20.13
# Developer: Deathsgift66
"""Legacy database helpers used by parts of the backend."""

from __future__ import annotations

import logging
import os
from typing import Any, Sequence

import psycopg2
from psycopg2.extras import RealDictCursor

logger = logging.getLogger("Thronestead.LegacyDB")

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost/postgres")


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
    def query(self, sql: str, params: Sequence[Any] | None = None) -> list[dict[str, Any]]:
        return query(sql, params)

    def execute(self, sql: str, params: Sequence[Any] | None = None) -> list[dict[str, Any]]:
        return execute(sql, params)


db = _DB()

__all__ = ["db", "query", "execute"]
