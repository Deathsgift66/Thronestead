# Project Name: Thronestead©
# File Name: test_admin_alerts_router.py
# Version:  7/1/2025 10:38
# Developer: Deathsgift66
from backend.routers.admin import (
    AlertFilters,
    AlertID,
    IPPayload,
    SuspendPayload,
    flag_ip,
    get_admin_alerts,
    mark_alert_handled,
    dismiss_alert,
    query_admin_alerts,
    suspend_user,
)


class DummyResult:
    def __init__(self, rows=None):
        self._rows = rows or []

    def fetchall(self):
        return self._rows


class DummyDB:
    def __init__(self):
        self.queries = []

    def execute(self, query, params=None):
        q = str(query)
        self.queries.append((q, params))
        if q.strip().lower().startswith("select is_admin"):
            return DummyResult([(True,)])
        return DummyResult()


def test_filters_included_in_query():
    db = DummyDB()
    get_admin_alerts(start="2025-01-01", end="2025-01-02", admin_id="a1", db=db)
    joined = " ".join(db.queries[0][0].split()).lower()
    assert "created_at >= :start" in joined
    assert db.queries[0][1]["start"] == "2025-01-01"


def test_account_alert_filters():
    db = DummyDB()
    filters = AlertFilters(start="2025-01-01", severity="high", kingdom="1")
    query_admin_alerts(filters, admin_id="a1", db=db)
    q = " ".join(db.queries[0][0].split()).lower()
    assert "timestamp >= :start" in q
    assert "severity = :severity" in q
    assert db.queries[0][1]["severity"] == "high"


def test_flag_ip_logs():
    db = DummyDB()
    flag_ip(IPPayload(ip="1.2.3.4"), admin_id="a1", db=db)
    assert any("insert into audit_log" in q[0].lower() for q in db.queries)
    assert any("insert into bans" in q[0].lower() for q in db.queries)


def test_suspend_user_logs():
    db = DummyDB()
    suspend_user(SuspendPayload(user_id="00000000-0000-4000-8000-000000000000"), admin_id="a1", db=db)
    assert any("insert into audit_log" in q[0].lower() for q in db.queries)


def test_mark_alert_logs():
    db = DummyDB()
    mark_alert_handled(AlertID(alert_id="11111111-1111-4111-8111-111111111111"), admin_id="a1", db=db)
    assert any("insert into audit_log" in q[0].lower() for q in db.queries)


def test_dismiss_alert_deletes_and_logs():
    class DB(DummyDB):
        def commit(self):
            self.committed = True

    db = DB()
    dismiss_alert(AlertID(alert_id="22222222-2222-4222-8222-222222222222"), admin_id="a1", db=db)
    joined = " ".join(db.queries[0][0].split()).lower()
    assert "delete from admin_alerts" in joined
    assert any("insert into audit_log" in q[0].lower() for q in db.queries)
