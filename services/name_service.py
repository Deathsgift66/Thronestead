import logging
from sqlalchemy import text
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

def name_in_use(db: Session, name: str) -> bool:
    """Return True if `name` is used for any player or kingdom name across public and auth tables."""
    if not name:
        return False

    normalized = name.strip().lower()

    # Short-circuit if there is no data in any upstream table
    try:
        has_data = db.execute(
            text(
                "SELECT (
                    EXISTS (SELECT 1 FROM users LIMIT 1) OR
                    EXISTS (SELECT 1 FROM kingdoms LIMIT 1) OR
                    EXISTS (SELECT 1 FROM auth.users LIMIT 1)
                )"
            )
        ).scalar()
    except Exception as e:
        logger.warning(f"Failed table existence check: {e}")
        has_data = True

    if has_data:
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
    else:
        return False

    return False
