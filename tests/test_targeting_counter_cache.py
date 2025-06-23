import pathlib
import sys
import types

# Set up dummy package structure for relative imports
backend_pkg = types.ModuleType("backend")
battle_pkg = types.ModuleType("backend.battle_engine")
backend_db = types.ModuleType("backend.db")
backend_db.db = None  # will be replaced in tests
sys.modules.setdefault("backend", backend_pkg)
sys.modules.setdefault("backend.battle_engine", battle_pkg)
sys.modules.setdefault("backend.db", backend_db)

module = types.ModuleType("backend.battle_engine.targeting")
module.__package__ = "backend.battle_engine"
module_path = pathlib.Path("backend/battle_engine/targeting.py")
exec(module_path.read_text(), module.__dict__)


class DummyDB:
    def __init__(self, rows=None):
        self.rows = rows or []
        self.calls = 0

    def query(self, sql, params=None):
        self.calls += 1
        return self.rows


def test_get_counter_multiplier_cached(monkeypatch):
    dummy = DummyDB(rows=[{"effectiveness_multiplier": 1.5}])
    monkeypatch.setattr(module, "db", dummy)
    module.get_counter_multiplier.cache_clear()

    first = module.get_counter_multiplier("archer", "cavalry")
    second = module.get_counter_multiplier("archer", "cavalry")

    assert first == 1.5
    assert second == 1.5
    assert dummy.calls == 1


def test_get_counter_multiplier_default(monkeypatch):
    dummy = DummyDB(rows=[])
    monkeypatch.setattr(module, "db", dummy)
    module.get_counter_multiplier.cache_clear()

    value = module.get_counter_multiplier("archer", "infantry")

    assert value == 1.0
    assert dummy.calls == 1
