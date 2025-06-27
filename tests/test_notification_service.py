import services.notification_service as ns
from backend.models import Notification

class DummyDB:
    def __init__(self, row=("1.1.1.1", "UA"), email="u@example.com"):
        self.row = row
        self.email = email
        self.added = None
    def execute(self, query, params):
        q = str(query).lower()
        class R:
            def __init__(self, value):
                self.value = value
            def fetchone(self_inner):
                return self_inner.value
        if "from user_active_sessions" in q:
            return R(self.row)
        if "select email" in q:
            return R((self.email,))
        return R(None)
    def add(self, obj):
        self.added = obj
    def commit(self):
        pass


def test_notify_new_login_sends_email(monkeypatch):
    db = DummyDB()
    captured = {}
    monkeypatch.setattr(ns, "send_email", lambda to, subject, body: captured.update({"to": to, "body": body}))
    ns.notify_new_login(db, "u1", "2.2.2.2", "Other")
    assert captured["to"] == "u@example.com"
    assert "2.2.2.2" in captured["body"]
    assert isinstance(db.added, Notification)


def test_notify_new_login_same_device(monkeypatch):
    db = DummyDB(row=("1.1.1.1", "UA"))
    called = {}
    monkeypatch.setattr(ns, "send_email", lambda *_a, **_k: called.update({"called": True}))
    ns.notify_new_login(db, "u1", "1.1.1.1", "UA")
    assert "called" not in called
    assert db.added is None
