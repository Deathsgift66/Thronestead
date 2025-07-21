from fastapi import HTTPException
from backend.routers import reauth


class DummySB:
    def __init__(self, mode="ok"):
        self.mode = mode
        self.auth = self

    def sign_in_with_password(self, *_args, **_kwargs):
        if self.mode == "error":
            return {"error": "bad"}
        if self.mode == "fail":
            raise Exception("fail")
        return {"session": {"access_token": "tok"}}

class DummyDB:
    def __init__(self, email="e@example.com", status=None):
        self.email = email
        self.status = status

    def execute(self, query, params=None):
        class R:
            def __init__(self, email, status):
                self._email = email
                self._status = status

            def fetchone(self_inner):
                return (self._email, self._status)

        return R(self.email, self.status)

    def commit(self):
        pass

class DummyReq:
    def __init__(self):
        self.headers = {}
        self.client = None


def test_reauth_success(monkeypatch):
    monkeypatch.setattr(reauth, "get_supabase_client", lambda: DummySB())
    monkeypatch.setattr(reauth, "create_reauth_token", lambda db, uid, ttl=300: "rtok")
    monkeypatch.setattr(reauth, "has_active_ban", lambda db, **_: False)
    db = DummyDB()
    payload = reauth.ReauthPayload(password="p")
    res = reauth.reauthenticate(DummyReq(), payload, user_id="u1", db=db)
    assert res["token"] == "rtok"
    assert res["expires_in"] == 300


def test_reauth_invalid_credentials(monkeypatch):
    monkeypatch.setattr(reauth, "get_supabase_client", lambda: DummySB("error"))
    monkeypatch.setattr(reauth, "has_active_ban", lambda db, **_: False)
    db = DummyDB()
    payload = reauth.ReauthPayload(password="p")
    try:
        reauth.reauthenticate(DummyReq(), payload, user_id="u1", db=db)
    except HTTPException as exc:
        assert exc.status_code == 401
    else:
        assert False


def test_reauth_banned_user(monkeypatch):
    monkeypatch.setattr(reauth, "get_supabase_client", lambda: DummySB())
    monkeypatch.setattr(reauth, "has_active_ban", lambda db, **_: True)
    db = DummyDB()
    payload = reauth.ReauthPayload(password="p")
    try:
        reauth.reauthenticate(DummyReq(), payload, user_id="u1", db=db)
    except HTTPException as exc:
        assert exc.status_code == 403
    else:
        assert False


def test_reauth_requires_otp(monkeypatch):
    monkeypatch.setattr(reauth, "get_supabase_client", lambda: DummySB())
    monkeypatch.setattr(reauth, "has_active_ban", lambda db, **_: False)
    db = DummyDB(status="suspicious")
    payload = reauth.ReauthPayload(password="p")
    try:
        reauth.reauthenticate(DummyReq(), payload, user_id="u1", db=db)
    except HTTPException as exc:
        assert exc.status_code == 401
    else:
        assert False


def test_reauth_otp_success(monkeypatch):
    monkeypatch.setattr(reauth, "get_supabase_client", lambda: DummySB())
    monkeypatch.setattr(reauth, "create_reauth_token", lambda db, uid, ttl=300: "tok")
    monkeypatch.setattr(reauth, "has_active_ban", lambda db, **_: False)
    db = DummyDB(status="suspicious")
    payload = reauth.ReauthPayload(password="p", otp="123456")
    res = reauth.reauthenticate(DummyReq(), payload, user_id="u1", db=db)
    assert res["token"] == "tok"


