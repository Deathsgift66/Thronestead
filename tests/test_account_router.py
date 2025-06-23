# Project Name: Thronestead©
# File Name: test_account_router.py
# Version 6.14.2025
# Developer: OpenAI Codex
from fastapi import HTTPException

from backend.routers import account


class DummyResult:
    def __init__(self, row=None):
        self._row = row

    def fetchone(self):
        return self._row


class DummyDB:
    def __init__(self, exists=True):
        self.exists = exists
        self.queries = []
        self.committed = False

    def execute(self, query, params=None):
        text = str(query).lower().strip()
        self.queries.append((text, params))
        if "from users" in text:
            return DummyResult((1,) if self.exists else None)
        return DummyResult()

    def commit(self):
        self.committed = True


def test_update_account_runs_update():
    db = DummyDB()
    payload = account.AccountUpdatePayload(display_name="Hero")
    result = account.update_account(payload, user_id="u1", db=db)
    assert result["message"] == "updated"
    joined = " ".join(db.queries[-2][0].split())
    assert "update users" in joined
    assert db.committed


def test_update_account_user_not_found():
    db = DummyDB(exists=False)
    try:
        account.update_account(account.AccountUpdatePayload(), user_id="u1", db=db)
    except HTTPException as exc:
        assert exc.status_code == 404
    else:
        assert False


def test_update_account_no_changes():
    db = DummyDB()
    result = account.update_account(account.AccountUpdatePayload(), user_id="u1", db=db)
    assert result["message"] == "no changes"
    # No commit should occur
    assert not db.committed
