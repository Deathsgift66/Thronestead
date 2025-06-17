# Project Name: Thronestead©
# File Name: test_world_map_router.py
# Version 6.13.2025.19.49
# Developer: Deathsgift66
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.db_base import Base
from backend.models import TerrainMap
from backend.routers import world_map


def setup_db():
    engine = create_engine("sqlite:///:memory:")
    Session = sessionmaker(bind=engine)
    Base.metadata.create_all(engine)
    return Session


def test_get_world_map_tiles_returns_latest():
    Session = setup_db()
    db = Session()
    db.add(
        TerrainMap(
            terrain_id=1,
            tile_map={"tiles": [{"x": 0, "y": 0, "terrain_type": "plains"}]},
            map_width=10,
            map_height=10,
        )
    )
    db.commit()

    result = world_map.get_world_map_tiles(db=db, user_id="u1")
    assert result["map_width"] == 10
    assert result["tile_map"]["tiles"][0]["terrain_type"] == "plains"
