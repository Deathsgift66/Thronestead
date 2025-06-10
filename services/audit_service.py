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


def log_alliance_activity(db: Session, alliance_id: int, user_id: str | None, action: str, description: str) -> None:
    """Insert a new alliance activity log entry."""
    db.execute(
        text(
            "INSERT INTO alliance_activity_log (alliance_id, user_id, action, description) "
            "VALUES (:aid, :uid, :act, :desc)"
        ),
        {"aid": alliance_id, "uid": user_id, "act": action, "desc": description},
    )
    db.commit()


def fetch_filtered_logs(
    db: Session,
    user_id: str | None = None,
    action: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    limit: int = 100,
) -> list[dict]:
    """Fetch audit logs with optional filters."""
    query = "SELECT log_id, user_id, action, details, created_at FROM audit_log WHERE 1=1"
    params = {"limit": limit}
    if user_id:
        query += " AND user_id = :uid"
        params["uid"] = user_id
    if action:
        query += " AND action ILIKE :act"
        params["act"] = f"%{action}%"
    if date_from:
        query += " AND created_at >= :date_from"
        params["date_from"] = date_from
    if date_to:
        query += " AND created_at <= :date_to"
        params["date_to"] = date_to
    query += " ORDER BY created_at DESC LIMIT :limit"
    rows = db.execute(text(query), params).fetchall()
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


def fetch_user_related_logs(db: Session, user_id: str) -> dict:
    """Return logs from multiple tables related to a specific user."""
    def q(sql: str) -> list[dict]:
        rows = db.execute(text(sql), {"uid": user_id}).fetchall()
        return [dict(r._mapping) if hasattr(r, "_mapping") else dict(zip(range(len(r)), r)) for r in rows]

    return {
        "global": fetch_filtered_logs(db, user_id=user_id, limit=100),
        "alliance": q("SELECT * FROM alliance_activity_log WHERE user_id = :uid ORDER BY created_at DESC"),
        "vault": q("SELECT * FROM alliance_vault_transaction_log WHERE user_id = :uid ORDER BY created_at DESC"),
        "grants": q("SELECT * FROM alliance_grants WHERE recipient_user_id = :uid ORDER BY created_at DESC"),
        "loans": q("SELECT * FROM alliance_loans WHERE borrower_user_id = :uid ORDER BY created_at DESC"),
        "training": q("SELECT * FROM training_history WHERE trained_by = :uid ORDER BY created_at DESC"),
    }
