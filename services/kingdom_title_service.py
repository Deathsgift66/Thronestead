import logging

try:
    from sqlalchemy import text
    from sqlalchemy.orm import Session
except ImportError:  # pragma: no cover - fallback when SQLAlchemy isn't installed
    text = lambda q: q  # type: ignore
    Session = object  # type: ignore


def award_title(db: Session, kingdom_id: int, title: str) -> None:
    """Grant a title to the kingdom if not already earned."""
    row = db.execute(
        text(
            "SELECT 1 FROM kingdom_titles "
            "WHERE kingdom_id = :kid AND title = :title"
        ),
        {"kid": kingdom_id, "title": title},
    ).fetchone()
    if row:
        return
    db.execute(
        text(
            "INSERT INTO kingdom_titles (kingdom_id, title) "
            "VALUES (:kid, :title)"
        ),
        {"kid": kingdom_id, "title": title},
    )
    db.commit()


def list_titles(db: Session, kingdom_id: int) -> list[dict]:
    """Return all titles earned by the kingdom ordered by newest first."""
    rows = db.execute(
        text(
            "SELECT title, awarded_at "
            "FROM kingdom_titles "
            "WHERE kingdom_id = :kid "
            "ORDER BY awarded_at DESC"
        ),
        {"kid": kingdom_id},
    ).fetchall()
    return [{"title": r[0], "awarded_at": r[1]} for r in rows]


def set_active_title(db: Session, kingdom_id: int, title: str | None) -> None:
    """Update the kingdom's active display title."""
    db.execute(
        text("UPDATE kingdoms SET active_title = :title WHERE kingdom_id = :kid"),
        {"title": title, "kid": kingdom_id},
    )
    db.commit()


def get_active_title(db: Session, kingdom_id: int) -> str | None:
    """Return the kingdom's currently active title."""
    row = db.execute(
        text("SELECT active_title FROM kingdoms WHERE kingdom_id = :kid"),
        {"kid": kingdom_id},
    ).fetchone()
    return row[0] if row else None
