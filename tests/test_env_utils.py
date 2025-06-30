import os

from backend.env_utils import get_env_var


def test_get_env_var_primary(monkeypatch):
    monkeypatch.setenv("SOME_KEY", "value")
    assert get_env_var("SOME_KEY") == "value"


def test_get_env_var_backup(monkeypatch):
    monkeypatch.delenv("SOME_KEY", raising=False)
    monkeypatch.setenv("BACKUP_SOME_KEY", "bvalue")
    assert get_env_var("SOME_KEY") == "bvalue"


def test_get_env_var_fallback_order(monkeypatch):
    monkeypatch.delenv("SOME_KEY", raising=False)
    monkeypatch.setenv("FALLBACK_SOME_KEY", "fvalue")
    monkeypatch.setenv("DEFAULT_SOME_KEY", "dvalue")
    assert get_env_var("SOME_KEY") == "fvalue"


def test_get_env_var_default(monkeypatch):
    monkeypatch.delenv("SOME_KEY", raising=False)
    monkeypatch.delenv("BACKUP_SOME_KEY", raising=False)
    monkeypatch.delenv("FALLBACK_SOME_KEY", raising=False)
    monkeypatch.delenv("DEFAULT_SOME_KEY", raising=False)
    assert get_env_var("SOME_KEY", default="x") == "x"

