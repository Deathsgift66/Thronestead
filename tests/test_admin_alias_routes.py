from backend.routers import admin, admin_dashboard


class DummyDB:
    pass


def test_get_admin_stats_calls_dashboard(monkeypatch):
    called = {}

    def fake_summary(admin_user_id, db):
        called["summary"] = True
        return {"ok": True}

    monkeypatch.setattr(admin_dashboard, "dashboard_summary", fake_summary)

    result = admin.get_admin_stats(admin_user_id="a1", db=DummyDB())
    assert called.get("summary") is True
    assert result["ok"] is True


def test_search_user_returns_players(monkeypatch):
    def fake_list(search, db):
        return {"players": [{"id": "p1"}]}

    monkeypatch.setattr(admin, "list_players", fake_list)

    result = admin.search_user(q="bob", db=DummyDB())
    assert result == [{"id": "p1"}]


def test_get_logs_calls_dashboard(monkeypatch):
    def fake_logs(**kwargs):
        return [{"log_id": 1}]

    monkeypatch.setattr(admin_dashboard, "get_audit_logs", fake_logs)

    result = admin.get_logs(admin_user_id="a1", db=DummyDB())
    assert result == [{"log_id": 1}]
