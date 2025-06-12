"""Optional SQLAlchemy database engine for migrations and tests."""

import logging
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from .db_base import Base

DATABASE_URL = os.getenv("DATABASE_URL")

if DATABASE_URL:
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    # Provide a backward compatible alias used in some modules/tests
    Session = SessionLocal
else:
    engine = None
    SessionLocal = None
    Session = None  # type: ignore
    logging.warning("DATABASE_URL not set; SQLAlchemy engine disabled")



def get_db():
    if SessionLocal is None:
        raise RuntimeError("DATABASE_URL not configured")

    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
