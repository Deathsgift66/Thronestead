import pytest
from fastapi import HTTPException

from backend.routers import alliance_members_view as amv


class Result:
    def __init__(self, data=None, error=None):
        self.data = data
        self.error = error


class DummyTable:
    def __init__(self, data=None, error=None):
        self._data = data
        self._error = error
        self._single = False

    def select(self, *_):
        return self

    def eq(self, *_args, **_kwargs):
        return self

    def single(self):
        self._single = True
        return self

    def execute(self):
        if self._error:
            return Result(error=self._error)
        return Result(data=self._data if self._single else [self._data])


class DummyRPC:
    def __init__(self, data=None, error=None):
        self._data = data
        self._error = error

    def execute(self):
        return Result(data=self._data, error=self._error)


class DummyClient:
    def __init__(self, user_row=None, rpc_data=None, rpc_error=None):
        self.user_row = user_row
        self.rpc_data = rpc_data
        self.rpc_error = rpc_error

    def table(self, name):
        if name == "users":
            return DummyTable(self.user_row)
        return DummyTable()

    def rpc(self, name, params):
        return DummyRPC(self.rpc_data, self.rpc_error)


def test_view_members_success(monkeypatch):
    client = DummyClient({"alliance_id": 1}, rpc_data=[{"user_id": "u1"}])
    monkeypatch.setattr(amv, "get_supabase_client", lambda: client)
    result = amv.view_alliance_members(user_id="u1")
    assert result["alliance_members"][0]["user_id"] == "u1"


def test_not_in_alliance(monkeypatch):
    client = DummyClient(None)
    monkeypatch.setattr(amv, "get_supabase_client", lambda: client)
    with pytest.raises(HTTPException) as exc:
        amv.view_alliance_members(user_id="u1")
    assert exc.value.status_code == 403


def test_rpc_error(monkeypatch):
    client = DummyClient({"alliance_id": 1}, rpc_error="fail")
    monkeypatch.setattr(amv, "get_supabase_client", lambda: client)
    with pytest.raises(HTTPException) as exc:
        amv.view_alliance_members(user_id="u1")
    assert exc.value.status_code == 500
