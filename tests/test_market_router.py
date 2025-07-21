from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.db_base import Base
from backend.models import MarketListing
from backend.routers.market import (
    BuyPayload,
    ListingPayload,
    buy_item,
    cancel_listing,
    get_listings,
    get_my_listings,
    list_item,
)


def setup_db():
    engine = create_engine("sqlite:///:memory:")
    Session = sessionmaker(bind=engine)
    Base.metadata.create_all(engine)
    return Session


def test_market_flow():
    Session = setup_db()
    db = Session()
    seller = "seller-1"

    res = list_item(
        ListingPayload(item_type="resource", item="wood", price=2.0, quantity=5),
        user_id=seller,
        db=db,
    )
    lid = res["listing_id"]
    listings = get_listings(db)["listings"]
    assert listings and listings[0]["listing_id"] == lid

    buy_item(BuyPayload(listing_id=lid, quantity=3), user_id="buyer", db=db)
    listing = db.query(MarketListing).get(lid)
    assert listing.quantity == 2

    buy_item(BuyPayload(listing_id=lid, quantity=2), user_id="buyer", db=db)
    assert db.query(MarketListing).get(lid) is None

    res2 = list_item(
        ListingPayload(item_type="resource", item="stone", price=1.0, quantity=1),
        user_id=seller,
        db=db,
    )
    mine = get_my_listings(user_id=seller, db=db)["listings"]
    assert {l["listing_id"] for l in mine} == {res2["listing_id"]}
    cancel_listing(res2["listing_id"], user_id=seller, db=db)
    assert db.query(MarketListing).get(res2["listing_id"]) is None
