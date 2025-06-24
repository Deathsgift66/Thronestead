import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.db_base import Base
from backend.models import KingdomResources, KingdomResourceTransfer
from services import resource_service


def setup_db():
    engine = create_engine("sqlite:///:memory:")
    Session = sessionmaker(bind=engine)
    Base.metadata.create_all(engine)
    return Session


def test_get_kingdom_resources_lock():
    Session = setup_db()
    db = Session()
    db.add(KingdomResources(kingdom_id=1, wood=5))
    db.commit()

    normal = resource_service.get_kingdom_resources(db, 1)
    locked = resource_service.get_kingdom_resources(db, 1, lock=True)
    assert normal == locked


def test_spend_resources_insufficient():
    Session = setup_db()
    db = Session()
    db.add(KingdomResources(kingdom_id=1, wood=5))
    db.commit()

    with pytest.raises(HTTPException):
        resource_service.spend_resources(db, 1, {"wood": 10})


def test_transfer_resource_logs_row():
    Session = setup_db()
    db = Session()
    db.add(KingdomResources(kingdom_id=1, wood=50))
    db.add(KingdomResources(kingdom_id=2, wood=10))
    db.commit()

    resource_service.transfer_resource(db, 1, 2, "wood", 20, reason="gift")

    transfer = db.query(KingdomResourceTransfer).first()
    assert transfer.from_kingdom_id == 1
    assert transfer.to_kingdom_id == 2
    assert transfer.resource_type == "wood"
    assert transfer.amount == 20
    assert transfer.reason == "gift"
