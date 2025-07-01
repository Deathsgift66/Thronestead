# Project Name: Thronestead©
# File Name: db_base.py
# Version:  7/1/2025 10:38
# Developer: Deathsgift66
"""Declarative base for all SQLAlchemy ORM models."""

from sqlalchemy.orm import declarative_base

# Shared base class used across the backend
Base = declarative_base()

__all__ = ["Base"]
