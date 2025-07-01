# Project Name: Thronestead©
# File Name: retry_webhooks.py
# Version:  7/1/2025 10:38
# Developer: Deathsgift66

import logging
from sqlalchemy import text

from backend.database import init_engine, SessionLocal
from services.webhook_service import send_webhook

logger = logging.getLogger(__name__)


def process_failures() -> None:
    init_engine()
    if SessionLocal is None:
        raise RuntimeError("Database not configured")
    db = SessionLocal()
    try:
        rows = db.execute(
            text(
                """
                SELECT failure_id, endpoint_url, payload, attempt_count
                  FROM webhook_failures
                 WHERE next_attempt_at <= now()
                 ORDER BY failure_id
                 LIMIT 50
                """
            )
        ).fetchall()
        for row in rows:
            success = send_webhook(row.endpoint_url, row.payload)
            if success:
                db.execute(
                    text("DELETE FROM webhook_failures WHERE failure_id = :fid"),
                    {"fid": row.failure_id},
                )
            else:
                db.execute(
                    text(
                        """
                        UPDATE webhook_failures
                           SET attempt_count = attempt_count + 1,
                               next_attempt_at = now() + interval '10 minutes'
                         WHERE failure_id = :fid
                        """
                    ),
                    {"fid": row.failure_id},
                )
        db.commit()
        if rows:
            logger.info("Processed %s webhook failures", len(rows))
    finally:
        db.close()


if __name__ == "__main__":
    process_failures()
