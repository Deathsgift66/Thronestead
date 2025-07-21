from contextlib import contextmanager
from backend.database import init_engine, SessionLocal

@contextmanager
def get_session():
    """Yield a database session, ensuring the engine is initialised."""
    init_engine()
    if SessionLocal is None:
        raise RuntimeError("DATABASE_URL not configured")
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
