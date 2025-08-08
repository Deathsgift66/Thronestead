import backend.battle_engine as be


def test_pathfinding_avoids_water():
    tiles = {}
    for x in range(5):
        for y in range(5):
            tiles[(x, y)] = be.TerrainTile(x, y)
    tiles[(2, 2)] = be.TerrainTile(2, 2, terrain_type="water", passable=False)
    path = be.compute_path((0, 0), (4, 4), tiles)
    assert path is not None
    coords = [(t.x, t.y) for t in path]
    assert (2, 2) not in coords
    assert coords[0] == (0, 0) and coords[-1] == (4, 4)
