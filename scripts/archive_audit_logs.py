# Project Name: Thronestead©
# File Name: archive_audit_logs.py
# Version:  7/1/2025 10:38
# Developer: Deathsgift66

from datetime import datetime, timedelta
import logging

from sqlalchemy import text

from .db_utils import get_session


logger = logging.getLogger(__name__)


def archive_logs() -> None:
    """Move audit_log entries older than 30 days to the archive."""
    with get_session() as db:
        cutoff = datetime.utcnow() - timedelta(days=30)
        db.execute(
            text(
                """
                INSERT INTO archived_audit_log (
                    log_id, user_id, action, details, ip_address, device_info, created_at
                )
                SELECT log_id, user_id, action, details, ip_address, device_info, created_at
                FROM audit_log
                WHERE created_at < :cutoff
                ON CONFLICT DO NOTHING
                """
            ),
            {"cutoff": cutoff},
        )
        db.execute(
            text("DELETE FROM audit_log WHERE created_at < :cutoff"),
            {"cutoff": cutoff},
        )
        db.commit()
        logger.info("Archived audit logs older than %s", cutoff)


if __name__ == "__main__":
    archive_logs()
