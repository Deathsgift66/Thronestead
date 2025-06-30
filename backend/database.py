# Project Name: Thronestead©
# File Name: database.py
# Version: 6.14.2025.20.13
# Developer: Deathsgift66
"""SQLAlchemy database configuration for Thronestead.

Provides ``engine`` and ``SessionLocal`` globals used throughout the
backend. Engine creation is optional and controlled via the
``DATABASE_URL`` environment variable.
"""

from __future__ import annotations

import logging
import os

from .env_utils import get_env
from typing import Generator, Optional

from fastapi import Request
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import sessionmaker

from .pg_settings import inject_claims_as_pg_settings

logger = logging.getLogger("Thronestead.Database")

DATABASE_URL = get_env(
    "DATABASE_URL",
    default="postgresql://postgres:postgres@localhost/postgres",
)

engine = None
SessionLocal: Optional[sessionmaker] = None
Session: Optional[sessionmaker] = None


def init_engine(db_url: Optional[str] = None) -> None:
    """Initialise the global SQLAlchemy engine and session factory."""
    global engine, SessionLocal, Session
    url = db_url or DATABASE_URL
    if not url:
        logger.warning("\u26a0\ufe0f DATABASE_URL is not set. SQLAlchemy is disabled.")
        engine = None
        SessionLocal = None
        Session = None
        return
    try:
        engine = create_engine(url, pool_pre_ping=True, pool_recycle=280)
        SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
        Session = SessionLocal
        logger.info("\u2705 SQLAlchemy engine initialized successfully.")
    except OperationalError as err:
        logger.error("\u274c Failed to initialize SQLAlchemy engine.")
        logger.exception(err)
        engine = None
        SessionLocal = None
        Session = None


# Initialise on import
init_engine()


def get_db(request: Request) -> Generator:
    """Yield a new SQLAlchemy session using request-scoped settings."""
    if SessionLocal is None:
        raise RuntimeError("DATABASE_URL not configured. Cannot create DB session.")

    db = SessionLocal()
    if request is not None:
        settings = inject_claims_as_pg_settings(request)
        for key, value in settings.items():
            try:
                db.execute(text(f"SET LOCAL {key} = :val"), {"val": value})
            except Exception:  # pragma: no cover - don't crash on bad settings
                logger.exception("Failed to set session variable %s", key)
    try:
        yield db
    finally:
        db.close()
