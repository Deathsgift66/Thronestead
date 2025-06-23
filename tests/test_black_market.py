# Project Name: Thronestead©
# File Name: test_black_market.py
# Version 6.13.2025.19.49
# Developer: Deathsgift66
import uuid

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.db_base import Base
from backend.models import BlackMarketListing
from backend.routers.black_market import (
    BuyPayload,
    CancelPayload,
    ListingPayload,
    buy_item,
    cancel_listing,
    get_market,
    place_item,
)


def setup_db():
    engine = create_engine("sqlite:///:memory:")
    Session = sessionmaker(bind=engine)
    Base.metadata.create_all(engine)
    return Session


def test_black_market_flow():
    Session = setup_db()
    db = Session()
    seller_id = str(uuid.uuid4())

    res = place_item(
        ListingPayload(item="gold", item_type="token", price=10.0, quantity=5),
        user_id=seller_id,
        db=db,
    )
    listing_id = res["listing_id"]

    market = get_market(db)
    assert market["listings"][0]["listing_id"] == listing_id

    buy_item(BuyPayload(listing_id=listing_id, quantity=3), user_id=seller_id, db=db)
    listing = db.query(BlackMarketListing).get(listing_id)
    assert listing.quantity == 2
    # Trade logging disabled; ensure quantity updated

    buy_item(BuyPayload(listing_id=listing_id, quantity=2), user_id=seller_id, db=db)
    assert db.query(BlackMarketListing).get(listing_id) is None
    # Listing fully purchased should be removed

    res2 = place_item(
        ListingPayload(item="gems", item_type="token", price=5.0, quantity=1),
        user_id=seller_id,
        db=db,
    )
    cancel_listing(
        CancelPayload(listing_id=res2["listing_id"]), user_id=seller_id, db=db
    )
    assert db.query(BlackMarketListing).get(res2["listing_id"]) is None
