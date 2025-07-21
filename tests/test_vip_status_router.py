"""Tests for the ``vip_status`` API router."""

from fastapi.testclient import TestClient

from backend.main import app
from backend.routers import vip_status_router


client = TestClient(app)


def test_get_vip_status_default(monkeypatch):
    """The endpoint should return an empty status when the service has no record."""

    def fake_get_status(db, user_id):
        assert user_id == "u1"
        return None

    monkeypatch.setattr(vip_status_router, "get_vip_status", fake_get_status)

    resp = client.get("/api/kingdom/vip_status", headers={"X-User-ID": "u1"})
    assert resp.status_code == 200
    assert resp.json() == {
        "vip_level": 0,
        "expires_at": None,
        "founder": False,
    }


def test_get_vip_status_record(monkeypatch):
    """The endpoint should proxy the service result when present."""

    record = {"vip_level": 2, "expires_at": None, "founder": True}

    def fake_get_status(db, user_id):
        assert user_id == "u1"
        return record

    monkeypatch.setattr(vip_status_router, "get_vip_status", fake_get_status)

    resp = client.get("/api/kingdom/vip_status", headers={"X-User-ID": "u1"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["vip_level"] == 2
    assert data["founder"] is True
