import uuid
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.database import Base
from backend.models import BlackMarketListing, TradeLog, User
from backend.routers.black_market import (
    ListingPayload,
    BuyPayload,
    CancelPayload,
    place_item,
    buy_item,
    cancel_listing,
    get_market,
)


def setup_db():
    engine = create_engine("sqlite:///:memory:")
    Session = sessionmaker(bind=engine)
    Base.metadata.create_all(engine)
    return Session


def create_user(db):
    uid = uuid.uuid4()
    user = User(
        user_id=uid,
        username="test",
        display_name="test",
        email="t@example.com",
    )
    db.add(user)
    db.commit()
    return str(uid)


def test_black_market_flow():
    Session = setup_db()
    db = Session()
    seller_id = create_user(db)

    res = place_item(
        ListingPayload(seller_id=seller_id, item="gold", price=10.0, quantity=5),
        db,
    )
    listing_id = res["listing_id"]

    market = get_market(db)
    assert market["listings"][0]["id"] == listing_id

    buy_item(BuyPayload(listing_id=listing_id, quantity=3, buyer_id=seller_id), db)
    listing = db.query(BlackMarketListing).get(listing_id)
    assert listing.quantity == 2
    tlog = db.query(TradeLog).first()
    assert tlog.quantity == 3 and tlog.trade_type == "black_market"

    buy_item(BuyPayload(listing_id=listing_id, quantity=2, buyer_id=seller_id), db)
    assert db.query(BlackMarketListing).get(listing_id) is None
    tlog2 = db.query(TradeLog).order_by(TradeLog.trade_id.desc()).first()
    assert tlog2.quantity == 2 and tlog2.trade_type == "black_market"

    res2 = place_item(
        ListingPayload(seller_id=seller_id, item="gems", price=5.0, quantity=1),
        db,
    )
    cancel_listing(
        CancelPayload(listing_id=res2["listing_id"], seller_id=seller_id), db
    )
    assert db.query(BlackMarketListing).get(res2["listing_id"]) is None
