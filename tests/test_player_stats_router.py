# Project Name: Thronestead©
# File Name: test_player_stats_router.py
# Version:  7/1/2025 10:38
# Developer: Deathsgift66

import pytest
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


class DummyDB:
    def __init__(self):
        self.queries = []
        self.row = None
        self.rows = []

    def execute(self, query, params=None):
        q = str(query).strip()
        self.queries.append(q)
        if "FROM kingdoms" in q:
            return DummyResult(row=self.row)
        if "FROM kingdom_troops" in q:
            return DummyResult(rows=self.rows)
        return DummyResult()


# -------------------------------------------------------------
# Tests
# -------------------------------------------------------------

def _grant_vip(monkeypatch):
    monkeypatch.setattr(
        player_stats, "get_vip_status", lambda db, uid: {"vip_level": 2, "expires_at": None, "founder": True}
    )
    monkeypatch.setattr(player_stats, "is_vip_active", lambda record: True)

def test_scores_requires_vip(monkeypatch):
    monkeypatch.setattr(player_stats, "get_vip_status", lambda db, uid: None)
    monkeypatch.setattr(player_stats, "is_vip_active", lambda record: False)
    with pytest.raises(HTTPException) as exc:
        player_stats.kingdom_scores(RequestStub(), 1, user_id="u1", db=DummyDB())
    assert exc.value.status_code == 403

def test_scores_returns_data(monkeypatch):
    _grant_vip(monkeypatch)
    db = DummyDB()
    db.row = (10, 20, 30, 40)
    result = player_stats.kingdom_scores(RequestStub(), 1, user_id="u1", db=db)
    assert result == {
        "kingdom_id": 1,
        "prestige_score": 10,
        "economy_score": 20,
        "military_score": 30,
        "diplomacy_score": 40,
    }


def test_scores_404(monkeypatch):
    _grant_vip(monkeypatch)
    db = DummyDB()
    with pytest.raises(HTTPException) as exc:
        player_stats.kingdom_scores(RequestStub(), 1, user_id="u1", db=db)
    assert exc.value.status_code == 404


def test_army_composition(monkeypatch):
    _grant_vip(monkeypatch)
    db = DummyDB()
    db.rows = [("infantry", 1, 100), ("archer", 1, 50)]
    result = player_stats.army_composition(RequestStub(), 1, user_id="u1", db=db)
    assert result == {
        "kingdom_id": 1,
        "army": [
            {"unit_type": "infantry", "unit_level": 1, "quantity": 100},
            {"unit_type": "archer", "unit_level": 1, "quantity": 50},
        ],
    }


class RequestStub:
    headers = {}
