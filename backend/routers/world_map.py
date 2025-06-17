# Project Name: Thronestead©
# File Name: world_map.py
# Version 6.13.2025.19.49
# Developer: Deathsgift66

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..database import get_db
from backend.models import TerrainMap
from ..security import verify_jwt_token

router = APIRouter(prefix="/api/world-map", tags=["world-map"])


@router.get("/tiles")
def get_world_map_tiles(
    db: Session = Depends(get_db),
    user_id: str = Depends(verify_jwt_token),
):
    """
    Return the most recent tile-based world map data for the client.

    This includes:
    - Full 2D grid layout from `tile_map`
    - World size (`map_width`, `map_height`)

    Notes:
    - Requires authentication
    - Returns empty tile array if no world map exists
    """
    latest_map = (
        db.query(TerrainMap)
        .order_by(TerrainMap.generated_at.desc())
        .first()
    )

    if not latest_map:
        return {
            "tile_map": {"tiles": []},
            "map_width": 0,
            "map_height": 0,
        }

    return {
        "tile_map": latest_map.tile_map,
        "map_width": latest_map.map_width,
        "map_height": latest_map.map_height,
    }
