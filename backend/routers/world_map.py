from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import TerrainMap
from ..security import verify_jwt_token

router = APIRouter(prefix="/api/world-map", tags=["world-map"])


@router.get("/tiles")
def get_world_map_tiles(
    db: Session = Depends(get_db),
    user_id: str = Depends(verify_jwt_token),
):
    """Return the latest world map tile data."""
    row = db.query(TerrainMap).order_by(TerrainMap.generated_at.desc()).first()
    if not row:
        return {"tile_map": {"tiles": []}, "map_width": 0, "map_height": 0}
    return {
        "tile_map": row.tile_map,
        "map_width": row.map_width,
        "map_height": row.map_height,
    }
