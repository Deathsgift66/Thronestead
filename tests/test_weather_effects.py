import types
from backend.battle_engine import vision, movement

class DummyDB:
    def query(self, *args, **kwargs):
        return [{"vision": 5}]
    def execute(self, *args, **kwargs):
        self.last = args

def test_vision_reduced_by_fog(monkeypatch):
    db = DummyDB()
    monkeypatch.setattr(vision, "db", db)
    unit = {
        "movement_id": 1,
        "kingdom_id": 1,
        "unit_type": "infantry",
        "position_x": 0,
        "position_y": 0,
    }
    enemy = {
        "movement_id": 2,
        "kingdom_id": 2,
        "position_x": 4,
        "position_y": 0,
    }
    terrain = [["plains"] * 5]
    vision.process_unit_vision(unit, [enemy], terrain, weather="fog")
    assert db.last[1][0] == 1  # update executed
    assert db.last[0][0] == []  # no visible enemies


def test_move_towards_rain_penalty():
    unit = {"position_x": 0, "position_y": 0}
    terrain = [["plains"] * 5]
    movement.move_towards(unit, 4, 0, 3, terrain, weather="rain")
    assert unit["position_x"] == 2
