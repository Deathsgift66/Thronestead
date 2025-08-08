import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

import sys
from pathlib import Path

# Ensure the repository root is on sys.path so that the ``backend`` package
# created for these exercises can be imported when tests are executed from the
# ``tests`` directory.
sys.path.append(str(Path(__file__).resolve().parent.parent))

from backend.database import Base


@pytest.fixture
def db_session():
    """Provide an in-memory SQLite session for tests."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    engine.execute(
        text(
            "CREATE TABLE IF NOT EXISTS audit_log (log_id INTEGER PRIMARY KEY AUTOINCREMENT, user_id TEXT, action TEXT, details TEXT, ip_address TEXT, device_info TEXT, created_at TEXT)"
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
