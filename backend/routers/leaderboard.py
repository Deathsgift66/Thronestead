from fastapi import APIRouter, Depends, HTTPException

from ..security import verify_jwt_token


from ..supabase_client import get_supabase_client
from ..database import get_db
from sqlalchemy.orm import Session
from sqlalchemy import func, case, or_
from backend.models import Alliance, AllianceWar, AllianceWarScore

router = APIRouter(prefix="/api/leaderboard", tags=["leaderboard"])


@router.get("/{type}")
def leaderboard(
    type: str,
    user_id: str = Depends(verify_jwt_token),
    db: Session = Depends(get_db),
):
    """Return leaderboard data."""
    if type == "alliances":
        win_case = case(
            (
                (AllianceWar.attacker_alliance_id == Alliance.alliance_id)
                & (AllianceWarScore.victor == "attacker"),
                1,
            ),
            (
                (AllianceWar.defender_alliance_id == Alliance.alliance_id)
                & (AllianceWarScore.victor == "defender"),
                1,
            ),
            else_=0,
        )
        loss_case = case(
            (
                (AllianceWar.attacker_alliance_id == Alliance.alliance_id)
                & (AllianceWarScore.victor == "defender"),
                1,
            ),
            (
                (AllianceWar.defender_alliance_id == Alliance.alliance_id)
                & (AllianceWarScore.victor == "attacker"),
                1,
            ),
            else_=0,
        )

        rows = (
            db.query(
                Alliance.alliance_id,
                Alliance.name.label("alliance_name"),
                Alliance.military_score,
                Alliance.economy_score,
                Alliance.diplomacy_score,
                func.coalesce(func.sum(win_case), 0).label("war_wins"),
                func.coalesce(func.sum(loss_case), 0).label("war_losses"),
            )
            .outerjoin(
                AllianceWar,
                or_(
                    AllianceWar.attacker_alliance_id == Alliance.alliance_id,
                    AllianceWar.defender_alliance_id == Alliance.alliance_id,
                ),
            )
            .outerjoin(
                AllianceWarScore,
                AllianceWarScore.alliance_war_id == AllianceWar.alliance_war_id,
            )
            .group_by(Alliance.alliance_id)
            .order_by(Alliance.military_score.desc())
            .limit(50)
            .all()
        )
        entries = [
            {
                "alliance_id": r.alliance_id,
                "alliance_name": r.alliance_name,
                "military_score": r.military_score or 0,
                "economy_score": r.economy_score or 0,
                "diplomacy_score": r.diplomacy_score or 0,
                "war_wins": r.war_wins or 0,
                "war_losses": r.war_losses or 0,
            }
            for r in rows
        ]
        return {"entries": entries}

    table_map = {
        "kingdoms": "leaderboard_kingdoms",
        "alliances": "leaderboard_alliances",
        "wars": "leaderboard_wars",
        "economy": "leaderboard_economy",
    }
    table = table_map.get(type)
    if not table:
        raise HTTPException(status_code=400, detail="invalid leaderboard type")

    supabase = get_supabase_client()
    try:
        result = (
            supabase.table(table)
            .select("*")
            .limit(50)
            .execute()
        )
    except Exception as exc:  # pragma: no cover - network/db errors
        raise HTTPException(status_code=500, detail="Failed to fetch leaderboard") from exc

    entries = getattr(result, "data", result) or []
    return {"entries": entries}

