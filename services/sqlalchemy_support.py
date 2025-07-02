from __future__ import annotations

"""Compatibility layer for optional SQLAlchemy imports."""

try:  # pragma: no cover - optional dependency
    from sqlalchemy import text
    from sqlalchemy.orm import Session
    from sqlalchemy.exc import SQLAlchemyError
except ImportError:  # pragma: no cover - SQLAlchemy not installed
    def text(q: str):  # type: ignore
        return q

    Session = object  # type: ignore
    SQLAlchemyError = Exception  # type: ignore

__all__ = ["text", "Session", "SQLAlchemyError"]
