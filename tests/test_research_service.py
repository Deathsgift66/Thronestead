# Project Name: Thronestead©
# File Name: test_research_service.py
# Version:  7/1/2025 10:38
# Developer: Deathsgift66
from datetime import datetime

import pytest

from services.research_service import (
    complete_finished_research,
    is_tech_completed,
    list_research,
    research_overview,
    start_research,
)


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
        self.rows = []
        self.row = None
        self.tech_row = (1, [], 0, None)
        self.castle_row = (1,)
        self.region_row = ("north",)
        self.catalog_rows = []
        self.commits = 0

    def execute(self, query, params=None):
        q = str(query).strip()
        self.queries.append((q, params))
        lower = q.lower()
        if "duration_hours" in lower:
            return DummyResult(row=self.tech_row)

        if "from tech_catalogue" in lower:
            return DummyResult(rows=self.catalog_rows)

        if "from kingdom_research_tracking" in lower:

            return DummyResult(rows=self.rows)
        return DummyResult()

    def commit(self):
        self.commits += 1


def test_start_research_inserts():
    db = DummyDB()
    ends_at = start_research(db, 1, "tech_a")
    assert any("INSERT INTO kingdom_research_tracking" in q for q, _ in db.queries)
    assert isinstance(ends_at, datetime)
    assert db.commits == 1


def test_start_research_prereq_check():
    db = DummyDB()
    db.tech_row = (1, ["req1"], 0, None)  # tech requires req1
    db.rows = []  # no completed techs
    with pytest.raises(ValueError):
        start_research(db, 1, "tech_a")


def test_start_research_level_requirement():
    db = DummyDB()
    db.tech_row = (1, [], 2, None)  # requires castle level 2
    db.castle_row = (1,)
    with pytest.raises(ValueError):
        start_research(db, 1, "tech_a")


def test_start_research_region_requirement():
    db = DummyDB()
    db.tech_row = (1, [], 0, "north")
    db.region_row = ("south",)
    with pytest.raises(ValueError):
        start_research(db, 1, "tech_a")


def test_complete_finished_updates():
    db = DummyDB()
    complete_finished_research(db, 1)
    assert any("UPDATE kingdom_research_tracking" in q for q, _ in db.queries)
    assert db.commits == 1


def test_list_and_check():
    db = DummyDB()
    db.rows = [("tech_a", "completed", 100, "2025-01-01")]
    results = list_research(db, 1)
    assert results[0]["tech_code"] == "tech_a"
    assert is_tech_completed(db, 1, "tech_a") is True


def test_list_research_category_filter():
    db = DummyDB()
    db.rows = [("tech_b", "active", 0, "2025-01-02")]
    results = list_research(db, 1, category="military")
    # last query executed should contain the join and category filter
    q = " ".join(db.queries[-1][0].split()).lower()
    assert "join tech_catalogue" in q
    assert "category = :category" in q
    assert db.queries[-1][1]["category"] == "military"
    assert results[0]["tech_code"] == "tech_b"


def test_research_overview_structure():
    db = DummyDB()
    db.rows = [("tech_a", "completed", 100, "2025-01-01")]
    # Tech catalogue rows returned when "FROM tech_catalogue" in query
    db.catalog_rows = [
        ("tech_a", [], 1, None),
        ("tech_b", ["tech_a"], 1, None),
    ]

    def execute_override(query, params=None):
        q = str(query).lower()
        db.queries.append((q, params))
        if "from tech_catalogue" in q:
            return DummyResult(rows=db.catalog_rows)
        if "from kingdom_research_tracking" in q:
            return DummyResult(rows=db.rows)
        if "kingdom_castle_progression" in q:
            return DummyResult(row=db.castle_row)
        if "from kingdoms where kingdom_id" in q:
            return DummyResult(row=db.region_row)
        return DummyResult()

    db.execute = execute_override  # type: ignore

    overview = research_overview(db, 1)
    assert overview["completed"][0]["tech_code"] == "tech_a"
    assert "tech_b" in overview["available"]
