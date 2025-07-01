# Project Name: Thronestead©
# File Name: admin_heartbeat.py
# Version:  7/1/2025 10:38
# Developer: Deathsgift66

from datetime import datetime, timedelta
import logging

from sqlalchemy import text

from backend.database import init_engine, SessionLocal

logger = logging.getLogger(__name__)


def send_heartbeat() -> None:
    """Insert heartbeat and log if previous ping missing."""
    init_engine()
    if SessionLocal is None:
        raise RuntimeError("Database not configured")
    db = SessionLocal()
    try:
        last = db.execute(
            text(
                "SELECT created_at FROM admin_alerts WHERE type = 'system_heartbeat'"
                " ORDER BY created_at DESC LIMIT 1"
            )
        ).scalar()
        if last and datetime.utcnow() - last > timedelta(minutes=30):
            db.execute(
                text(
                    "INSERT INTO admin_alerts (type, severity, message)"
                    " VALUES ('system_heartbeat_missing', 'high', 'No heartbeat for over 30m')"
                )
            )
        db.execute(
            text(
                "INSERT INTO admin_alerts (type, severity, message)"
                " VALUES ('system_heartbeat', 'info', 'heartbeat ping')"
            )
        )
        db.commit()
        logger.info("Heartbeat recorded")
    finally:
        db.close()


if __name__ == "__main__":
    send_heartbeat()
