from backend.battle_engine import resolver_full as rf

class DummyResult:
    def __init__(self, rows=None):
        self._rows = rows or []
    def first(self):
        return self._rows[0]

class DummyDB:
    def __init__(self):
        self.queries = []
        self.units = [
            {
                "movement_id": 1,
                "kingdom_id": 1,
                "unit_type": "catapult",
                "quantity": 10,
                "speed": 1,
                "class": "siege",
                "can_build_bridge": False,
                "can_damage_castle": True,
                "position_x": 0,
                "position_y": 0,
                "stance": "advance_engage",
            }
        ]
    def query(self, sql, params=None):
        s = str(sql).lower()
        if "from unit_movements" in s:
            return self.units
        if "from alliance_war_participants" in s:
            return [{"kingdom_id": 1}]
        if "from terrain_map" in s:
            return DummyResult([{"tile_map": [["plains"]]}])
        if "from kingdom_troop_slots" in s:
            return [
                {
                    "kingdom_id": 1,
                    "morale_bonus_buildings": 0,
                    "morale_bonus_tech": 0,
                    "morale_bonus_events": 0,
                }
            ]
        return []
    def execute(self, sql, params=None):
        self.queries.append((str(sql).lower(), params))
        return []

def test_kingdom_tick_damages_castle(monkeypatch):
    db = DummyDB()
    monkeypatch.setattr(rf, "db", db)
    called = {}
    monkeypatch.setattr(rf, "check_victory_condition_kingdom", lambda wid: called.setdefault("wid", wid))
    rf.process_kingdom_war_tick({"war_id": 1, "battle_tick": 0, "castle_hp": 50})
    assert any("castle_damage" in q[0] for q in db.queries)
    upd = next(p for q, p in db.queries if "update wars_tactical" in q)
    assert upd[1] == 0
    assert called.get("wid") == 1

def test_alliance_tick_damages_castle(monkeypatch):
    db = DummyDB()
    monkeypatch.setattr(rf, "db", db)
    monkeypatch.setattr(rf, "update_alliance_war_score", lambda aid: None)
    called = {}
    monkeypatch.setattr(rf, "check_victory_condition_alliance", lambda aid: called.setdefault("aid", aid))
    rf.process_alliance_war_tick({"alliance_war_id": 2, "battle_tick": 0, "castle_hp": 50})
    assert any("alliance_war_combat_logs" in q[0] for q in db.queries)
    upd = next(p for q, p in db.queries if "update alliance_wars" in q)
    assert upd[1] == 0
    assert called.get("aid") == 2
