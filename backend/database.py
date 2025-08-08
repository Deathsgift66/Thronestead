"""Minimal database utilities for tests.

The production application would define engine and session management here,
but the test suite only requires access to the SQLAlchemy ``Base`` for
creating tables in an in-memory SQLite database.
"""

from sqlalchemy.orm import declarative_base

Base = declarative_base()
