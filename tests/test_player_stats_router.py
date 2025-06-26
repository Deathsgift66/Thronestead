# Project Name: Thronestead©
# File Name: test_player_stats_router.py
from datetime import datetime, timedelta

from fastapi import HTTPException

from backend.routers import player_stats


class DummyResult:
    def __init__(self, row=None, rows=None):
        self._row = row
        self._rows = rows or []

    def fetchone(self):
        return self._row

    def fetchall(self):
        return self._rows

    def mappings(self):
        return self


class DummyDB:
    def __init__(self):
        self.vip_row = (2, datetime.utcnow() + timedelta(days=1), False)
        self.score_row = (10, 5, 7, 3)
        self.troop_rows = [("Spearman", 1, 50)]
        self.calls = []

    def execute(self, query, params=None):
        q = str(query)
        self.calls.append(q)
        if "FROM kingdom_vip_status" in q:
            return DummyResult(row=self.vip_row)
        if "FROM kingdoms" in q:
            return DummyResult(row=self.score_row)
        if "FROM kingdom_troops" in q:
            return DummyResult(rows=self.troop_rows)
        return DummyResult()

    def commit(self):
        pass


def test_scores_requires_vip():
    db = DummyDB()
    db.vip_row = None
    try:
        player_stats.kingdom_scores(kingdom_id=1, user_id="u1", db=db)
    except HTTPException as exc:
        assert exc.status_code == 403
    else:
        assert False, "Expected HTTPException"


def test_scores_returns_data():
    db = DummyDB()
    res = player_stats.kingdom_scores(kingdom_id=1, user_id="u1", db=db)
    assert res["prestige_score"] == 10
    assert res["economy_score"] == 5


def test_army_composition_returns_rows():
    db = DummyDB()
    res = player_stats.army_composition(kingdom_id=1, user_id="u1", db=db)
    assert res["army"][0]["unit_type"] == "Spearman"

