# File Name: test_public_kingdom_router.py
# Version 6.14.2025
# Developer: OpenAI Codex

from backend.routers import public_kingdom
from fastapi import HTTPException

class DummyResult:
    def __init__(self, row=None):
        self._row = row
    def fetchone(self):
        return self._row

class DummyDB:
    def __init__(self, row=None, villages=0):
        self.row = row
        self.villages = villages
        self.queries = []
    def execute(self, query, params=None):
        self.queries.append((str(query), params))
        q = str(query).lower()
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
