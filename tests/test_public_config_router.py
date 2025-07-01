# Project Name: Thronestead©
# File Name: test_public_config_router.py
# Version:  7/1/2025 10:38
# Developer: Deathsgift66
import os

from backend.routers import public_config


class DummyResult:
    def __init__(self, row):
        self._row = row

    def fetchone(self):
        return self._row


class DummyDB:
    def execute(self, query, params=None):
        key = params.get("k")
        if key == "maintenance_mode":
            return DummyResult(("true",))
        if key == "fallback_override":
            return DummyResult(("false",))
        return DummyResult(None)


def test_public_config_returns_env_values():
    os.environ["SUPABASE_URL"] = "url"
    os.environ["SUPABASE_ANON_KEY"] = "anon"
    db = DummyDB()
    result = public_config.public_config(db=db)
    assert result == {
        "SUPABASE_URL": "url",
        "SUPABASE_ANON_KEY": "anon",
        "MAINTENANCE_MODE": True,
        "FALLBACK_OVERRIDE": False,
    }
