# Project Name: Kingmakers Rise©
# File Name: all_models.py
# Version: 6.13.2025.19.49
# Developer: Deathsgift66

"""
This module uses SQLAlchemy's automap to dynamically reflect all tables from the connected database.
It provides an easy way to access all models without explicitly declaring them.
"""

from sqlalchemy.ext.automap import automap_base
from sqlalchemy.exc import SQLAlchemyError

from .database import engine
from . import logger

# Create a base class for automapped models
AutomapBase = automap_base()

try:
    # Reflect all tables from the connected database engine
    AutomapBase.prepare(engine, reflect=True)
    logger.info("✅ Successfully reflected all tables into AutomapBase.")

    # Expose the mapped classes (tables) as an accessible dictionary-like namespace
    models = AutomapBase.classes

except SQLAlchemyError as e:
    logger.error(f"❌ Error reflecting database models: {e}")
    raise

# Example usage:
#   user_table = models.users
#   kingdom_table = models.kingdoms
