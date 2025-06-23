# Project Name: Thronestead©
# File Name: test_black_market_routes.py
# Version 6.13.2025.19.49
# Developer: Deathsgift66
from backend.routers.black_market_routes import (
    PurchasePayload,
    get_listings,
    history,
    purchase,
)


def test_purchase_flow():
    listings = get_listings()["listings"]
    assert listings
    lid = listings[0]["id"]
    purchase(PurchasePayload(listing_id=lid, quantity=2, kingdom_id="demo-kingdom"))
    updated = get_listings()["listings"][0]["stock_remaining"]
    assert updated == listings[0]["stock_remaining"] - 2
    hist = history("demo-kingdom")["trades"]
    assert hist and hist[0]["quantity"] == 2
