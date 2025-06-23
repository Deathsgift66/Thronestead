import asyncio

from backend.routers import vip_status_router


class DummyDB:
    def __init__(self, row=None):
        self.row = row

    def query(self, sql, params=None):
        return [self.row] if self.row else []


def test_get_vip_status_default():
    vip_status_router.db = DummyDB(None)
    result = asyncio.run(vip_status_router.get_vip_status(user_id="u1"))
    assert result["vip_level"] == 0


def test_get_vip_status_record():
    vip_status_router.db = DummyDB({"vip_level": 2, "founder": True})
    result = asyncio.run(vip_status_router.get_vip_status(user_id="u1"))
    assert result["vip_level"] == 2
    assert result["founder"] is True
