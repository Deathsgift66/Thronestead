import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from backend.db_base import Base


@pytest.fixture
def db_session():
    """Provide an in-memory SQLite session for tests."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    engine.execute(
        text(
            "CREATE TABLE IF NOT EXISTS audit_log (log_id INTEGER PRIMARY KEY AUTOINCREMENT, user_id TEXT, action TEXT, details TEXT, created_at TEXT)"
        )
    )
    Session = sessionmaker(bind=engine)
    session = Session()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def supabase_user():
    """Return a simple confirmed Supabase user representation."""
    return {"id": "u-test", "email": "user@example.com"}
