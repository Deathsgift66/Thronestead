from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker

from backend.db_base import Base


def test_index_definitions_present():
    engine = create_engine("sqlite:///:memory:")
    sessionmaker(bind=engine)
    Base.metadata.create_all(engine)

    inspector = inspect(engine)
    terrain_indexes = inspector.get_indexes("terrain_map")
    unit_indexes = inspector.get_indexes("unit_movements")

    terrain_names = {idx["name"] for idx in terrain_indexes}
    unit_names = {idx["name"] for idx in unit_indexes}

    assert "idx_terrain_map_war_id" in terrain_names
    assert "idx_unit_movements_war_id" in unit_names
