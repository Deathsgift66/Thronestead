# Project Name: Thronestead©
# File Name: database.py
# Version:  7/1/2025 10:38
# Developer: Deathsgift66
"""SQLAlchemy database configuration for Thronestead.

Provides ``engine`` and ``SessionLocal`` globals used throughout the
backend. Engine creation is optional and controlled via the
``DATABASE_URL`` environment variable.
"""

from __future__ import annotations

import logging
from typing import Generator, Optional

from fastapi import Request
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import declarative_base, sessionmaker

from .pg_settings import inject_claims_as_pg_settings
from .env_utils import get_env_var

logger = logging.getLogger("Thronestead.Database")

# Declarative base used for all ORM models
Base = declarative_base()

# Default to local Postgres when DATABASE_URL isn't provided
DATABASE_URL = get_env_var(
    "DATABASE_URL",
    default="postgresql://postgres:postgres@localhost/postgres",
)
READ_REPLICA_URL = get_env_var("READ_REPLICA_URL")

engine = None
SessionLocal: Optional[sessionmaker] = None


def _create_sessionmaker(url: str) -> tuple[Engine, sessionmaker]:
    """Return a new engine and bound sessionmaker for ``url``."""
    eng = create_engine(url, pool_pre_ping=True, pool_recycle=280)
    return eng, sessionmaker(bind=eng, autoflush=False, autocommit=False)


def init_engine(db_url: Optional[str] = None) -> None:
    """Initialise the global SQLAlchemy engine and session factory."""
    global engine, SessionLocal
    primary = db_url or DATABASE_URL
    if not primary:
        logger.warning("\u26a0\ufe0f DATABASE_URL is not set. SQLAlchemy is disabled.")
        engine = SessionLocal = None
        return

    candidates = [primary]
    if READ_REPLICA_URL and db_url is None:
        logger.info("\u27f3 Attempting read replica failover.")
        candidates.append(READ_REPLICA_URL)

    for candidate in candidates:
        try:
            engine, SessionLocal = _create_sessionmaker(candidate)
            logger.info("\u2705 SQLAlchemy engine initialized successfully.")
            return
        except OperationalError as err:
            logger.error("\u274c Failed to connect to %s", candidate)
            logger.exception(err)

    engine = SessionLocal = None


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


__all__ = [
    "Base",
    "engine",
    "SessionLocal",
    "init_engine",
    "get_db",
]
