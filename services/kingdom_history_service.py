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


def fetch_full_history(db: Session, kingdom_id: int) -> dict:
    """Return aggregated historical data for a kingdom."""

    def single(query: str) -> dict:
        row = (
            db.execute(text(query), {"kid": kingdom_id}).mappings().fetchone()
        )
        return dict(row) if row else {}

    def many(query: str) -> list[dict]:
        rows = (
            db.execute(text(query), {"kid": kingdom_id}).mappings().fetchall()
        )
        return [dict(r) for r in rows]

    return {
        "core": single(
            "SELECT kingdom_name, ruler_name, created_at, motto, region "
            "FROM kingdoms WHERE kingdom_id = :kid"
        ),
        "timeline": many(
            "SELECT event_type, event_details, event_date "
            "FROM kingdom_history_log WHERE kingdom_id = :kid "
            "ORDER BY event_date DESC"
        ),
        "wars_fought": many(
            "SELECT war_id, attacker_id, defender_id, war_reason, outcome, "
            "start_date, end_date FROM wars "
            "WHERE attacker_kingdom_id = :kid OR defender_kingdom_id = :kid "
            "ORDER BY start_date DESC"
        ),
        "achievements": many(
            "SELECT k.achievement_code, c.name, c.description, k.awarded_at "
            "FROM kingdom_achievements k "
            "JOIN kingdom_achievement_catalogue c "
            "ON k.achievement_code = c.achievement_code "
            "WHERE k.kingdom_id = :kid"
        ),
        "titles": many(
            "SELECT title, awarded_at FROM kingdom_titles "
            "WHERE kingdom_id = :kid ORDER BY awarded_at DESC"
        ),
        "research_log": many(
            "SELECT tech_code, status, progress, ends_at "
            "FROM kingdom_research_tracking WHERE kingdom_id = :kid"
        ),
        "quests_log": many(
            "SELECT quest_code, status, started_at, ends_at "
            "FROM quest_kingdom_tracking WHERE kingdom_id = :kid "
            "ORDER BY started_at DESC"
        ),
        "training_log": many(
            "SELECT unit_name, quantity, completed_at "
            "FROM training_history WHERE kingdom_id = :kid "
            "ORDER BY completed_at DESC"
        ),
        "projects_log": many(
            "SELECT p.project_code, c.name, p.starts_at, p.ends_at "
            "FROM projects_player p "
            "JOIN project_player_catalogue c ON p.project_code = c.project_code "
            "WHERE p.kingdom_id = :kid ORDER BY p.starts_at DESC"
        ),
    }
