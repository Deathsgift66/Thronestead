import backend.battle_engine as be


def test_line_of_sight_blocked_by_mountain():
    tiles = {
        (0, 0): be.TerrainTile(0, 0),
        (0, 1): be.TerrainTile(0, 1),
        (0, 2): be.TerrainTile(0, 2, terrain_type="mountain", passable=False, elevation=2),
        (0, 3): be.TerrainTile(0, 3),
    }
    a = be.WarUnit(unit_id="A", side="red", x=0, y=0, range=5)
    b = be.WarUnit(unit_id="B", side="blue", x=0, y=3, range=5)
    visible = be.compute_visibility(a, [a, b], tiles, max_range=5)
    assert b not in visible
