import logging
from sqlalchemy import text
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


def name_in_use(db: Session, name: str) -> bool:
    """Return True if ``name`` is used for any player or kingdom."""
    if not name:
        return False

    normalized = name.strip().lower()

    # Check public tables
    row = db.execute(
        text(
            """
            SELECT 1 FROM (
                SELECT lower(trim(username)) AS n FROM users
                UNION ALL
                SELECT lower(trim(display_name)) FROM users
                UNION ALL
                SELECT lower(trim(kingdom_name)) FROM kingdoms
                UNION ALL
                SELECT lower(trim(ruler_name)) FROM kingdoms
            ) x WHERE n = :n LIMIT 1
            """
        ),
        {"n": normalized},
    ).fetchone()
    if row:
        return True

    # Attempt to check auth.users if available
    try:
        row = db.execute(
            text(
                """
                SELECT 1 FROM auth.users
                WHERE lower(trim(raw_user_meta_data->>\"display_name\")) = :n
                   OR lower(trim(raw_user_meta_data->>\"username\")) = :n
                LIMIT 1
                """
            ),
            {"n": normalized},
        ).fetchone()
        if row:
            return True
    except Exception:
        logger.debug("auth.users table unavailable")

    return False
