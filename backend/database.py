# Project Name: Thronestead©
# File Name: database.py
# Version: 6.13.2025.19.49
# Developer: Deathsgift66

"""
This module configures the SQLAlchemy engine and session factory
for database access in Thronestead©.

Used for real-time backend services, migrations, and test environments.
"""

import os
import logging
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import OperationalError
from typing import Generator, Optional
from fastapi import Request

from .pg_settings import inject_claims_as_pg_settings

# Initialize logger
logger = logging.getLogger("Thronestead.Database")

# Load database URL from environment (e.g., Render, local .env, CI/CD)
DATABASE_URL = os.getenv("DATABASE_URL")

# Globals (for app-wide SQLAlchemy access)
engine = None
SessionLocal: Optional[sessionmaker] = None
Session: Optional[sessionmaker] = None


def init_engine(db_url: Optional[str] = None) -> None:
    """Initialize the global SQLAlchemy engine and session factory."""
    global engine, SessionLocal, Session
    url = db_url or DATABASE_URL
    if not url:
        logger.warning("⚠️ DATABASE_URL is not set. SQLAlchemy is disabled.")
        engine = None
        SessionLocal = None
        Session = None
        return
    try:
        engine = create_engine(
            url,
            pool_pre_ping=True,
            pool_recycle=280,
        )
        SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
        Session = SessionLocal
        logger.info("✅ SQLAlchemy engine initialized successfully.")
    except OperationalError as err:
        logger.error("❌ Failed to initialize SQLAlchemy engine.")
        logger.exception(err)
        engine = None
        SessionLocal = None
        Session = None


# Initialize engine on import for normal application startup
init_engine()

def get_db(request: Request = None) -> Generator:
    """
    Yields a new SQLAlchemy session and ensures it closes after use.

    Usage:
        with next(get_db()) as db:
            # use db session
    """
    if SessionLocal is None:
        raise RuntimeError("DATABASE_URL not configured. Cannot create DB session.")

    db = SessionLocal()
    if request is not None:
        settings = inject_claims_as_pg_settings(request)
        for key, value in settings.items():
            try:
                db.execute(text(f"SET LOCAL {key} = :val"), {"val": value})
            except Exception:
                logger.exception("Failed to set session variable %s", key)
    try:
        yield db
    finally:
        db.close()
