from backend.routers.black_market_routes import get_listings, purchase, history, PurchasePayload


def test_purchase_flow():
    listings = get_listings()["listings"]
    assert listings
    lid = listings[0]["id"]
    purchase(PurchasePayload(listing_id=lid, quantity=2, kingdom_id="demo-kingdom"))
    updated = get_listings()["listings"][0]["stock_remaining"]
    assert updated == listings[0]["stock_remaining"] - 2
    hist = history("demo-kingdom")["trades"]
    assert hist and hist[0]["quantity"] == 2
