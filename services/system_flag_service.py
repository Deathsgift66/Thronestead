"""System flag retrieval helpers."""
from __future__ import annotations
import logging

from services.sqlalchemy_support import Session, text

logger = logging.getLogger(__name__)


def get_flag(db: Session, key: str, default: bool = False) -> bool:
    """Return boolean status for ``key`` from system_flags."""
    try:
        row = db.execute(
            text("SELECT flag_value FROM system_flags WHERE flag_key = :k"),
            {"k": key},
        ).fetchone()
    except Exception:  # pragma: no cover - DB errors
        logger.exception("Failed retrieving system flag %s", key)
        return default
    if not row:
        return default
    val = str(row[0]).strip().lower()
    return val in {"1", "true", "yes", "on"}
