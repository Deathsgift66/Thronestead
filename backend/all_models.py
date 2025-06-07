from sqlalchemy.ext.automap import automap_base

from .database import engine

AutomapBase = automap_base()

# Reflect all tables present in the connected database. This allows accessing
# every table without declaring explicit SQLAlchemy models for each one.
AutomapBase.prepare(engine, reflect=True)

models = AutomapBase.classes
