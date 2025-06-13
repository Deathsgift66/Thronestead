# Project Name: Kingmakers Rise©
# File Name: test_strategic_tick_service.py
# Version 6.13.2025.19.49
# Developer: Deathsgift66
from services.strategic_tick_service import (
    update_project_progress,
    expire_treaties,
    activate_pending_wars,
    check_war_status,
)


class DummyResult:
    def __init__(self, rows=None, rowcount=0):
        self._rows = rows or []
        self.rowcount = rowcount

    def fetchall(self):
        return self._rows


class DummyDB:
    def __init__(self):
        self.queries = []
        self.rows = []
        self.commits = 0

    def execute(self, query, params=None):
        q = str(query).strip()
        self.queries.append(q)
        if q.startswith("SELECT war_id FROM wars"):
            return DummyResult(rows=self.rows)
        return DummyResult(rowcount=1)

    def commit(self):
        self.commits += 1


def test_project_progress_updates():
    db = DummyDB()
    count = update_project_progress(db)
    assert count == 1
    assert any("projects_alliance_in_progress" in q for q in db.queries)
    assert db.commits == 2


def test_expire_treaties_runs_updates():
    db = DummyDB()
    count = expire_treaties(db)
    assert count == 2
    joined = " ".join(db.queries)
    assert "alliance_treaties" in joined and "kingdom_treaties" in joined
    assert db.commits == 2


def test_activate_pending_wars_selects_and_updates():
    db = DummyDB()
    db.rows = [(5,), (6,)]
    count = activate_pending_wars(db)
    assert count == 2
    joined = " ".join(db.queries)
    assert "SELECT war_id FROM wars" in joined
    assert "UPDATE wars SET status='active'" in joined
    assert "event_notification_log" in joined
    assert db.commits == 4


def test_check_war_status_updates():
    db = DummyDB()
    count = check_war_status(db)
    assert count == 2
    assert any("UPDATE wars SET status='concluded'" in q for q in db.queries)
    assert any("UPDATE alliance_wars SET war_status='concluded'" in q for q in db.queries)
    assert db.commits == 2
