import logging

try:
    from sqlalchemy import text
    from sqlalchemy.orm import Session
except ImportError:  # pragma: no cover - SQLAlchemy optional
    text = lambda q: q  # type: ignore
    Session = object  # type: ignore
from datetime import datetime


def upsert_vip_status(
    db: Session,
    user_id: str,
    vip_level: int,
    expires_at: datetime | None = None,
    founder: bool = False,
) -> None:
    """Insert or update a user's VIP status."""
    db.execute(
        text(
            """
            INSERT INTO kingdom_vip_status (user_id, vip_level, expires_at, founder)
            VALUES (:uid, :lvl, :exp, :founder)
            ON CONFLICT (user_id)
            DO UPDATE SET vip_level = EXCLUDED.vip_level,
                          expires_at = EXCLUDED.expires_at,
                          founder = EXCLUDED.founder
            """
        ),
        {"uid": user_id, "lvl": vip_level, "exp": expires_at, "founder": founder},
    )
    db.commit()


def get_vip_status(db: Session, user_id: str) -> dict | None:
    """Return VIP status record for the given user."""
    row = db.execute(
        text(
            "SELECT vip_level, expires_at, founder "
            "FROM kingdom_vip_status WHERE user_id = :uid"
        ),
        {"uid": user_id},
    ).fetchone()
    if not row:
        return None
    return {"vip_level": row[0], "expires_at": row[1], "founder": row[2]}


def is_vip_active(record: dict | None) -> bool:
    """Return True if the provided VIP record represents an active VIP state."""
    if not record:
        return False
    if record.get("founder"):
        return True
    exp = record.get("expires_at")
    level = record.get("vip_level", 0)
    if level and exp and exp > datetime.utcnow():
        return True
    return False
