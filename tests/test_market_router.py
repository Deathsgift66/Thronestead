# Project Name: Kingmakers Rise©
# File Name: test_market_router.py
# Version 6.13.2025.19.49
# Developer: Deathsgift66
from backend.routers import market
from backend.routers.market import ListingAction


class DummyTable:
    def __init__(self, data=None):
        self._data = data or []
        self._filters = []
        self._single = False
        self._delete = False

    def select(self, *_args):
        return self

    def order(self, *_args, **kwargs):
        return self

    def limit(self, _n):
        return self

    def eq(self, column, value):
        if self._delete:
            self._data = [r for r in self._data if r.get(column) != value]
        else:
            self._filters.append((column, value))
        return self

    def single(self):
        self._single = True
        return self

    def delete(self):
        self._delete = True
        return self

    def _apply(self):
        data = self._data
        for col, val in self._filters:
            data = [d for d in data if d.get(col) == val]
        return data

    def execute(self):
        if self._delete:
            return {"data": None}
        data = self._apply()
        if self._single:
            return {"data": data[0] if data else None}
        return {"data": data}


class DummyClient:
    def __init__(self, tables):
        self.tables = tables

    def table(self, name):
        t = self.tables.get(name)
        if isinstance(t, DummyTable):
            return t
        return DummyTable(t)


def test_listings_returns_rows():
    data = [{"listing_id": 1, "item_name": "Wood", "quantity": 10, "price": 5, "seller_name": "A", "seller_id": "u1"}]
    market.get_supabase_client = lambda: DummyClient({"market_listings": data})
    result = market.listings(user_id="u1")
    assert result["listings"][0]["item_name"] == "Wood"


def test_my_listings_filters_user():
    data = [
        {"listing_id": 1, "item_name": "Wood", "quantity": 10, "price": 5, "seller_name": "A", "seller_id": "u1"},
        {"listing_id": 2, "item_name": "Stone", "quantity": 5, "price": 3, "seller_name": "B", "seller_id": "u2"},
    ]
    market.get_supabase_client = lambda: DummyClient({"market_listings": data})
    res = market.my_listings(user_id="u1")
    assert len(res["listings"]) == 1 and res["listings"][0]["listing_id"] == 1


def test_cancel_listing_removes_row():
    table = DummyTable([{"listing_id": 1, "seller_id": "u1"}])
    market.get_supabase_client = lambda: DummyClient({"market_listings": table})
    market.cancel_listing(ListingAction(listing_id=1), user_id="u1")
    assert table._data == []


def test_history_returns_rows():
    logs = [{"item_name": "Wood", "quantity": 2, "price": 5, "buyer_name": "A", "seller_name": "B", "completed_at": "2025-01-01"}]
    market.get_supabase_client = lambda: DummyClient({"trade_logs": logs})
    result = market.history(user_id="u1")
    assert result["trades"][0]["item_name"] == "Wood"
