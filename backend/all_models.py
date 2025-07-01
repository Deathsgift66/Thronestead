# Comment
# Project Name: Thronestead©
# File Name: all_models.py
# Version: 7/1/2025 10:31
# Developer: Deathsgift66

"""
Dynamically reflect and expose all SQLAlchemy models from the connected PostgreSQL database.
This allows access to all game-related tables without manually defining ORM classes.

Integrates error logging and safe initialization for production use.
"""

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import configure_mappers

from . import logger
from .database import engine

# Create automap base class for runtime reflection
AutomapBase = automap_base()

try:
    # Reflect the database schema and prepare mapped classes
    logger.info("🔄 Reflecting database schema via SQLAlchemy Automap...")
    AutomapBase.prepare(engine, reflect=True)

    # Optional: force early mapper configuration (catches issues before runtime)
    configure_mappers()

    # Access to all reflected table models (as attributes)
    models = AutomapBase.classes
    logger.info("✅ All models reflected successfully. Ready for access.")

except SQLAlchemyError as e:
    logger.error("❌ Database reflection failed during AutomapBase.prepare()")
    logger.exception(e)
    raise

# Optional: Example direct model access (uncomment to inspect)
# print(dir(models))
# print(models.users)
# print(models.kingdoms)

# Export for use in FastAPI routes, services, etc.
__all__ = ["AutomapBase", "models"]
