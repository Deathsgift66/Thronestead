from datetime import datetime, timedelta

import pytest

from services.modifier_stack_service import compute_modifier_stack
from services.progression_service import get_total_modifiers


class DummyResult:
    def __init__(self, row=None, rows=None):
        self._row = row
        self._rows = rows or []

    def fetchone(self):
        return self._row

    def fetchall(self):
        return self._rows


class DummyDB:
    def __init__(self, village_rows):
        self.village_rows = village_rows

    def execute(self, query, params=None):
        q = str(query).lower()
        params = params or {}
        if "from village_modifiers" in q:
            kid = params.get("kid")
            active = []
            now = datetime.utcnow()
            for row in self.village_rows:
                if row["kingdom_id"] != kid:
                    continue
                exp = row.get("expires_at")
                if exp is not None and exp <= now:
                    continue
                active.append(
                    (
                        row.get("resource_bonus"),
                        row.get("troop_bonus"),
                        row.get("construction_speed_bonus", 0),
                        row.get("defense_bonus", 0),
                        row.get("trade_bonus", 0),
                        row.get("source"),
                        row.get("stacking_rules", {}),
                    )
                )
            return DummyResult(rows=active)
        if "kingdom_villages" in q and "count" in q:
            return DummyResult((0,))
        return DummyResult()

    def commit(self):
        pass


def test_village_modifier_additive_and_expiration():
    rows = [
        {
            "kingdom_id": 1,
            "resource_bonus": {"wood": 5},
            "troop_bonus": {},
            "source": "m1",
            "stacking_rules": {"resource_bonus": "additive"},
            "expires_at": None,
        },
        {
            "kingdom_id": 1,
            "resource_bonus": {"wood": 3},
            "troop_bonus": {},
            "source": "m2",
            "stacking_rules": {},
            "expires_at": None,
        },
        {
            "kingdom_id": 1,
            "resource_bonus": {"wood": 10},
            "troop_bonus": {},
            "source": "expired",
            "stacking_rules": {},
            "expires_at": datetime.utcnow() - timedelta(hours=1),
        },
    ]
    db = DummyDB(rows)
    stack = compute_modifier_stack(db, 1)
    assert stack["resource_bonus"]["wood"]["total"] == 8
    assert len(stack["resource_bonus"]["wood"]["sources"]) == 2


def test_get_total_modifiers_includes_village_rows():
    rows = [
        {
            "kingdom_id": 1,
            "resource_bonus": {"wood": 2},
            "troop_bonus": {},
            "source": "m1",
            "stacking_rules": {"resource_bonus": "additive"},
            "expires_at": None,
        },
        {
            "kingdom_id": 1,
            "resource_bonus": {"wood": 4},
            "troop_bonus": {},
            "source": "m2",
            "stacking_rules": {"resource_bonus": "additive"},
            "expires_at": None,
        },
    ]
    db = DummyDB(rows)
    mods = get_total_modifiers(db, 1, use_cache=False)
    assert mods["resource_bonus"]["wood"] == 6
