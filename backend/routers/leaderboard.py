# Project Name: Thronestead©
# File Name: leaderboard.py
# Version 6.16.2025.21.20
# Developer: Codex

"""
Project: Thronestead ©
File: leaderboard.py
Role: API routes for leaderboard.
Version: 2025-06-21
"""

from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy import case, func, or_
from sqlalchemy.orm import Session

from backend.models import Alliance, AllianceWar, AllianceWarScore, User

from ..database import get_db
from ..security import verify_jwt_token
from ..supabase_client import get_supabase_client


def _optional_user(
    authorization: str | None = Header(None),
    x_user_id: str | None = Header(None),
) -> str | None:
    """Return user ID if valid headers are provided."""
    if authorization and x_user_id:
        try:
            return verify_jwt_token(authorization=authorization, x_user_id=x_user_id)
        except HTTPException:
            return None
    return None


router = APIRouter(prefix="/api/leaderboard", tags=["leaderboard"])


@router.get("/{category}")
def get_leaderboard(
    category: str,
    limit: int = 100,
    user_id: str | None = Depends(_optional_user),
    db: Session = Depends(get_db),
):
    """
    🏆 Universal leaderboard route.

    Categories:
      - kingdoms: Total prestige
      - alliances: Combined alliance score
      - wars: War score (victories, kills, contribution)
      - economy: Total economic output (resources produced/traded)
    """
    if category == "alliances":
        # Define win and loss cases for alliances in wars
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

        # Query leaderboard stats for alliances
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
            .limit(limit)
            .all()
        )
        user_alliance_id = None
        if user_id:
            result = db.query(User.alliance_id).filter(User.user_id == user_id).first()
            user_alliance_id = result[0] if result else None

        entries = []
        for r in rows:
            entries.append(
                {
                    "alliance_id": r.alliance_id,
                    "alliance_name": r.alliance_name,
                    "military_score": r.military_score or 0,
                    "economy_score": r.economy_score or 0,
                    "diplomacy_score": r.diplomacy_score or 0,
                    "war_wins": r.war_wins or 0,
                    "war_losses": r.war_losses or 0,
                    "is_self": bool(
                        user_alliance_id and r.alliance_id == user_alliance_id
                    ),
                }
            )

        return {"category": category, "entries": entries}

    # Supported Supabase views for other leaderboard types
    table_map = {
        "kingdoms": "leaderboard_kingdoms",
        "wars": "leaderboard_wars",
        "economy": "leaderboard_economy",
    }

    table = table_map.get(category)
    if not table:
        raise HTTPException(status_code=400, detail="Invalid leaderboard category")

    supabase = get_supabase_client()
    try:
        result = (
            supabase.table(table)
            .select("*")
            .order("rank", asc=True)
            .limit(limit)
            .execute()
        )
        entries = getattr(result, "data", result) or []
    except Exception as exc:
        raise HTTPException(
            status_code=500, detail="Failed to fetch leaderboard"
        ) from exc

    # Mark current user if present
    if user_id:
        for e in entries:
            if str(e.get("user_id")) == str(user_id):
                e["is_self"] = True
            else:
                e.setdefault("is_self", False)

    return {"category": category, "entries": entries}
