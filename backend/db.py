from __future__ import annotations

"""Lightweight database helper used by the battle engine."""

from typing import Any, Iterable, List, Mapping

from sqlalchemy import text

from .database import SessionLocal


class _DB:
    """Provide simple ``query`` and ``execute`` helpers."""

    def query(self, sql: str, params: Iterable[Any] | None = None) -> List[Mapping[str, Any]]:
        """Execute ``sql`` returning rows as dictionaries."""
        params = tuple(params or [])
        with SessionLocal() as session:
            result = session.execute(text(sql), params)
            return [dict(row._mapping) for row in result]

    def execute(self, sql: str, params: Iterable[Any] | None = None) -> None:
        """Execute ``sql`` committing the transaction."""
        params = tuple(params or [])
        with SessionLocal() as session:
            session.execute(text(sql), params)
            session.commit()


db = _DB()
