from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from ..database import get_db
from .progression_router import get_user_id, get_kingdom_id

router = APIRouter(prefix="/api/village-master", tags=["village_master"])


@router.get("/overview")
def village_overview(
    user_id: str = Depends(get_user_id),
    db: Session = Depends(get_db),
):
    """Return aggregated village data for the player's kingdom."""
    kid = get_kingdom_id(db, user_id)
    rows = db.execute(
        text(
            """
            SELECT v.village_id, v.village_name,
                   COUNT(b.building_id) AS building_count,
                   COALESCE(SUM(b.level),0) AS total_level
            FROM kingdom_villages v
            LEFT JOIN village_buildings b ON b.village_id = v.village_id
            WHERE v.kingdom_id = :kid
            GROUP BY v.village_id
            ORDER BY v.created_at
            """
        ),
        {"kid": kid},
    ).fetchall()

    return {
        "overview": [
            {
                "village_id": r[0],
                "village_name": r[1],
                "building_count": int(r[2]),
                "total_level": int(r[3]),
            }
            for r in rows
        ]
    }
