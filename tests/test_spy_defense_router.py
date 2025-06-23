import asyncio

from fastapi import HTTPException

from backend.routers.spy import get_spy_defense


class DummyResult:
    def __init__(self, row=None):
        self._row = row

    def fetchone(self):
        return self._row


class DummyDB:
    def __init__(self, kingdom_row=None, defense_row=None):
        self.kingdom_row = kingdom_row
        self.defense_row = defense_row

    def execute(self, query, params=None):
        q = str(query).lower()
        if "from kingdoms" in q:
            return DummyResult(self.kingdom_row)
        if "from spy_defense" in q:
            return DummyResult(self.defense_row)
        return DummyResult()


def test_get_spy_defense_not_found():
    db = DummyDB(kingdom_row=None)
    try:
        asyncio.run(get_spy_defense(user_id="u1", db=db))
    except HTTPException as e:
        assert e.status_code == 404


def test_get_spy_defense_success():
    db = DummyDB(kingdom_row=(1,), defense_row={"kingdom_id": 1, "defense_rating": 5})
    result = asyncio.run(get_spy_defense(user_id="u1", db=db))
    assert result["defense_rating"] == 5
