import logging

try:
    from sqlalchemy import text
    from sqlalchemy.orm import Session
except ImportError:  # pragma: no cover - fallback when SQLAlchemy isn't installed
    text = lambda q: q  # type: ignore
    Session = object  # type: ignore


def award_achievement(db: Session, kingdom_id: int, achievement_code: str):
    """Award an achievement if not already earned.

    Returns the reward JSON if newly awarded, otherwise ``None``.
    """
    row = db.execute(
        text(
            "SELECT 1 FROM kingdom_achievements "
            "WHERE kingdom_id = :kid AND achievement_code = :code"
        ),
        {"kid": kingdom_id, "code": achievement_code},
    ).fetchone()

    if row:
        return None

    db.execute(
        text(
            "INSERT INTO kingdom_achievements (kingdom_id, achievement_code) "
            "VALUES (:kid, :code)"
        ),
        {"kid": kingdom_id, "code": achievement_code},
    )

    reward_row = db.execute(
        text(
            "SELECT reward FROM kingdom_achievement_catalogue "
            "WHERE achievement_code = :code"
        ),
        {"code": achievement_code},
    ).fetchone()

    db.commit()

    return reward_row[0] if reward_row else None


def list_achievements(db: Session, kingdom_id: int):
    """Return all achievements with unlock status for a kingdom."""
    rows = db.execute(
        text(
            """
            SELECT c.achievement_code, c.name, c.description, c.category,
                   c.reward, c.points, c.is_hidden, a.awarded_at
            FROM kingdom_achievement_catalogue c
            LEFT JOIN kingdom_achievements a
              ON c.achievement_code = a.achievement_code
             AND a.kingdom_id = :kid
            ORDER BY c.category, c.achievement_code
            """
        ),
        {"kid": kingdom_id},
    ).fetchall()

    achievements = []
    for r in rows:
        if r[6] and r[7] is None:
            # hidden and not yet unlocked
            continue
        achievements.append(
            {
                "achievement_code": r[0],
                "name": r[1],
                "description": r[2],
                "category": r[3],
                "reward": r[4],
                "points": r[5],
                "is_hidden": r[6],
                "awarded_at": r[7],
            }
        )
    return achievements
