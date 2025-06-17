# Project Name: Thronestead©
# File Name: db.py
# Version: 6.13.2025.19.49
# Developer: Deathsgift66

"""
Lightweight synchronous SQL helper for internal battle engine and real-time backend ops.
Provides simplified query and execution methods using SQLAlchemy core with session management.
"""

from typing import Any, Iterable, List, Mapping, Optional
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from .database import SessionLocal
from . import logger


class _DB:
    """
    Provides lightweight `query()` and `execute()` methods for
    raw SQL access with automatic session handling.
    """

    def query(self, sql: str, params: Optional[Iterable[Any]] = None) -> List[Mapping[str, Any]]:
        """
        Executes a raw SQL query and returns the result rows as dictionaries.

        Args:
            sql (str): SQL SELECT statement to run.
            params (Iterable[Any], optional): Parameters to pass into the SQL query.

        Returns:
            List[Mapping[str, Any]]: List of rows returned as key-value dicts.
        """
        try:
            with SessionLocal() as session:
                result = session.execute(text(sql), tuple(params or []))
                return [dict(row._mapping) for row in result]
        except SQLAlchemyError as e:
            logger.error(f"❌ DB QUERY ERROR — SQL: {sql} | Params: {params}")
            logger.exception(e)
            return []

    def execute(self, sql: str, params: Optional[Iterable[Any]] = None) -> None:
        """
        Executes a raw SQL command (INSERT, UPDATE, DELETE) with commit.

        Args:
            sql (str): SQL statement to run.
            params (Iterable[Any], optional): Parameters to pass into the SQL statement.
        """
        try:
            with SessionLocal() as session:
                session.execute(text(sql), tuple(params or []))
                session.commit()
                logger.debug(f"✅ DB EXECUTE SUCCESS — SQL: {sql} | Params: {params}")
        except SQLAlchemyError as e:
            logger.error(f"❌ DB EXECUTE ERROR — SQL: {sql} | Params: {params}")
            logger.exception(e)
            raise


# Exported database utility instance
db = _DB()
