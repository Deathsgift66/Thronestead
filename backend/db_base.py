# Project Name: Thronestead©
# File Name: db_base.py
# Version: 6.13.2025.19.49
# Developer: Deathsgift66

"""
Base declarative class used for all custom SQLAlchemy ORM model definitions.
"""

from sqlalchemy.orm import declarative_base

# Declarative base to be used across all ORM models
Base = declarative_base()

# Optional: Set custom naming conventions (for Alembic compatibility, if used in migrations)
# from sqlalchemy import MetaData
# Base = declarative_base(metadata=MetaData(naming_convention={
#     "ix": "ix_%(column_0_label)s",
#     "uq": "uq_%(table_name)s_%(column_0_name)s",
#     "ck": "ck_%(table_name)s_%(constraint_name)s",
#     "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
#     "pk": "pk_%(table_name)s"
# }))

__all__ = ["Base"]
