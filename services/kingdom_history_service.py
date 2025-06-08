try:
    from sqlalchemy import text
    from sqlalchemy.orm import Session
except Exception:  # pragma: no cover - fallback when SQLAlchemy isn't installed
    text = lambda q: q  # type: ignore
    Session = object  # type: ignore


def log_event(db: Session, kingdom_id: int, event_type: str, event_details: str) -> None:
    """Insert a new kingdom history log entry."""
    db.execute(
        text(
            "INSERT INTO kingdom_history_log (kingdom_id, event_type, event_details) "
            "VALUES (:kid, :etype, :details)"
        ),
        {"kid": kingdom_id, "etype": event_type, "details": event_details},
    )
    db.commit()


def fetch_history(db: Session, kingdom_id: int, limit: int = 50) -> list[dict]:
    """Fetch history log entries for a kingdom ordered by newest first."""
    rows = db.execute(
        text(
            "SELECT log_id, event_type, event_details, event_date "
            "FROM kingdom_history_log "
            "WHERE kingdom_id = :kid "
            "ORDER BY event_date DESC "
            "LIMIT :limit"
        ),
        {"kid": kingdom_id, "limit": limit},
    ).fetchall()

    return [
        {
            "log_id": r[0],
            "event_type": r[1],
            "event_details": r[2],
            "event_date": r[3],
        }
        for r in rows
    ]
