import os

from backend.env_utils import get_env_var


def test_get_env_var_primary(monkeypatch):
    monkeypatch.setenv("SOME_KEY", "value")
    assert get_env_var("SOME_KEY") == "value"


def test_get_env_var_variant(monkeypatch):
    monkeypatch.delenv("SOME_KEY", raising=False)
    monkeypatch.setenv("VITE_SOME_KEY", "vvalue")
    assert get_env_var("SOME_KEY") == "vvalue"


def test_get_env_var_default(monkeypatch):
    monkeypatch.delenv("SOME_KEY", raising=False)
    monkeypatch.delenv("VITE_SOME_KEY", raising=False)
    monkeypatch.delenv("PUBLIC_SOME_KEY", raising=False)
    monkeypatch.delenv("PUBLIC_VITE_SOME_KEY", raising=False)
    assert get_env_var("SOME_KEY", default="x") == "x"

