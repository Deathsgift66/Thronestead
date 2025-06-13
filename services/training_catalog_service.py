"""Helpers for reading the training_catalog table."""

import logging

try:
    from sqlalchemy import text
    from sqlalchemy.orm import Session
except ImportError:  # pragma: no cover - fallback if SQLAlchemy missing
    text = lambda q: q  # type: ignore
    Session = object  # type: ignore


def list_units(db: Session) -> list[dict]:
    """Return all units in the training catalog ordered by tier."""
    rows = db.execute(
        text("SELECT * FROM training_catalog ORDER BY tier ASC")
    ).fetchall()
    return [dict(row._mapping) for row in rows]
