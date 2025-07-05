import logging
from sqlalchemy import text
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

def name_in_use(db: Session, name: str) -> bool:
    """Return True if `name` is used for any player or kingdom name across public and auth tables."""
    if not name:
        return False

    normalized = name.strip().lower()

    # ✅ Check in public.users and public.kingdoms
    try:
        row = db.execute(
            text(
                """
                SELECT 1 FROM (
                    SELECT LOWER(TRIM(username)) AS n FROM users
                    UNION
                    SELECT LOWER(TRIM(display_name)) AS n FROM users
                    UNION
                    SELECT LOWER(TRIM(kingdom_name)) AS n FROM kingdoms
                    UNION
                    SELECT LOWER(TRIM(ruler_name)) AS n FROM kingdoms
                ) AS x
                WHERE n = :n
                LIMIT 1
                """
            ),
            {"n": normalized},
        ).fetchone()
        if row:
            return True
    except Exception as e:
        logger.warning(f"Failed public name check: {e}")

    # ✅ Attempt to check in auth.users (Supabase users)
    try:
        row = db.execute(
            text(
                """
                SELECT 1 FROM auth.users
                WHERE LOWER(TRIM(raw_user_meta_data->>'display_name')) = :n
                   OR LOWER(TRIM(raw_user_meta_data->>'username')) = :n
                LIMIT 1
                """
            ),
            {"n": normalized},
        ).fetchone()
        if row:
            return True
    except Exception:
        logger.debug("auth.users table unavailable or not accessible")

    return False
