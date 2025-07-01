# Project Name: Thronestead©
# File Name: test_noble_houses_router.py
# Version:  7/1/2025 10:38
# Developer: Deathsgift66
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.db_base import Base
from backend.routers.noble_houses import (
    HousePayload,
    create_house,
    delete_house,
    get_house,
    list_houses,
    update_house,
)


def setup_db():
    engine = create_engine("sqlite:///:memory:")
    Session = sessionmaker(bind=engine)
    Base.metadata.create_all(engine)
    return Session


def test_full_crud_flow():
    Session = setup_db()
    db = Session()

    res = create_house(HousePayload(name="Stark"), db=db)
    hid = res["house_id"]

    house = get_house(hid, db=db)
    assert house["name"] == "Stark"

    update_house(hid, HousePayload(name="Stark", motto="Winter is Coming"), db=db)
    updated = get_house(hid, db=db)
    assert updated["motto"] == "Winter is Coming"

    result = delete_house(hid, db=db)
    assert result["message"] == "deleted"
    assert list_houses(db=db)["houses"] == []
