try:
    from sqlalchemy import text
    from sqlalchemy.orm import Session
except Exception:  # pragma: no cover - fallback when SQLAlchemy isn't installed
    text = lambda q: q  # type: ignore
    Session = object  # type: ignore


def log_action(db: Session, user_id: str | None, action: str, details: str) -> None:
    """Insert a new audit log entry."""
    db.execute(
        text(
            "INSERT INTO audit_log (user_id, action, details) "
            "VALUES (:uid, :act, :det)"
        ),
        {"uid": user_id, "act": action, "det": details},
    )
    db.commit()


def fetch_logs(db: Session, user_id: str | None = None, limit: int = 100) -> list[dict]:
    """Fetch audit log entries, optionally filtered by user."""
    if user_id:
        rows = db.execute(
            text(
                "SELECT log_id, user_id, action, details, created_at "
                "FROM audit_log "
                "WHERE user_id = :uid "
                "ORDER BY created_at DESC "
                "LIMIT :limit"
            ),
            {"uid": user_id, "limit": limit},
        ).fetchall()
    else:
        rows = db.execute(
            text(
                "SELECT log_id, user_id, action, details, created_at "
                "FROM audit_log "
                "ORDER BY created_at DESC "
                "LIMIT :limit"
            ),
            {"limit": limit},
        ).fetchall()

    return [
        {
            "log_id": r[0],
            "user_id": r[1],
            "action": r[2],
            "details": r[3],
            "created_at": r[4],
        }
        for r in rows
    ]
