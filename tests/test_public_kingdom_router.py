# File Name: test_public_kingdom_router.py
# Version 6.14.2025
# Developer: OpenAI Codex

from fastapi import HTTPException

from backend.routers import public_kingdom


class DummyResult:
    def __init__(self, row=None, rows=None):
        self._row = row
        self._rows = rows or []

    def fetchone(self):
        return self._row

    def fetchall(self):
        return self._rows


class DummyDB:
    def __init__(self, row=None, villages=0, lookup_rows=None):
        self.row = row
        self.villages = villages
        self.lookup_rows = lookup_rows or []
        self.queries = []

    def execute(self, query, params=None):
        self.queries.append((str(query), params))
        q = str(query).lower()
        if "select kingdom_id" in q and "from kingdoms" in q and "kingdom_name" in q:
            return DummyResult(rows=self.lookup_rows)
        if "from kingdoms" in q:
            return DummyResult(self.row)
        if "from kingdom_villages" in q:
            return DummyResult((self.villages,))
        return DummyResult()


def test_public_profile_returns_data():
    row = (
        "Realm",
        "Ruler",
        "Motto",
        "pic.png",
        10,
        5,
        6,
        7,
        False,
    )
    db = DummyDB(row=row, villages=3)
    result = public_kingdom.public_profile(1, db=db)
    assert result["military_score"] == 5
    assert result["village_count"] == 3


def test_public_profile_not_found():
    db = DummyDB(row=None)
    try:
        public_kingdom.public_profile(1, db=db)
    except HTTPException as e:
        assert e.status_code == 404
    else:
        assert False


def test_public_profile_banned_hidden():
    db = DummyDB(row=None)
    try:
        public_kingdom.public_profile(1, db=db)
    except HTTPException as e:
        assert e.status_code == 404
    else:
        assert False


def test_kingdom_lookup_returns_rows():
    rows = [(1, "Alpha"), (2, "Beta")]
    db = DummyDB(lookup_rows=rows)
    result = public_kingdom.kingdom_lookup(db=db)
    assert result == [
        {"kingdom_id": 1, "kingdom_name": "Alpha"},
        {"kingdom_id": 2, "kingdom_name": "Beta"},
    ]
