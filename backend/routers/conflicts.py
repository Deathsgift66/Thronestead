from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from ..database import get_db
from .progression_router import get_kingdom_id
from ..security import verify_jwt_token


from ..supabase_client import get_supabase_client


router = APIRouter(prefix="/api/conflicts", tags=["conflicts"])


def get_alliance_id(db: Session, user_id: str) -> int:
    row = db.execute(
        text("SELECT alliance_id FROM users WHERE user_id = :uid"),
        {"uid": user_id},
    ).fetchone()
    if not row or row[0] is None:
        raise HTTPException(status_code=404, detail="Alliance not found")
    return row[0]


@router.get("/kingdom")
def list_kingdom_wars(
    user_id: str = Depends(verify_jwt_token),
    db: Session = Depends(get_db),
):
    kid = get_kingdom_id(db, user_id)
    supabase = get_supabase_client()
    res = (
        supabase.table("wars")
        .select("*")
        .or_(f"attacker_kingdom_id.eq.{kid},defender_kingdom_id.eq.{kid}")
        .execute()
    )
    return {"wars": getattr(res, "data", res) or []}


@router.get("/alliance")
def list_alliance_wars(
    user_id: str = Depends(verify_jwt_token),
    db: Session = Depends(get_db),
):
    aid = get_alliance_id(db, user_id)
    supabase = get_supabase_client()
    res = (
        supabase.table("alliance_wars")
        .select("*")
        .or_(f"attacker_alliance_id.eq.{aid},defender_alliance_id.eq.{aid}")
        .execute()
    )
    return {"wars": getattr(res, "data", res) or []}


@router.get("/war/{war_id}/details")
def get_war_details(
    war_id: int,
    user_id: str = Depends(verify_jwt_token),
    db: Session = Depends(get_db),
):
    supabase = get_supabase_client()
    war_res = (
        supabase.table("wars")
        .select("*")
        .eq("war_id", war_id)
        .single()
        .execute()
    )
    war = getattr(war_res, "data", war_res)
    if not war:
        raise HTTPException(status_code=404, detail="War not found")

    kid = get_kingdom_id(db, user_id)
    if war.get("attacker_kingdom_id") != kid and war.get("defender_kingdom_id") != kid:
        raise HTTPException(status_code=403, detail="Access denied")

    score_res = (
        supabase.table("war_scores")
        .select("attacker_score, defender_score, victor")
        .eq("war_id", war_id)
        .single()
        .execute()
    )
    score = getattr(score_res, "data", score_res) or {}

    return {
        "war_id": war.get("war_id"),
        "attacker_name": war.get("attacker_name"),
        "defender_name": war.get("defender_name"),
        "phase": war.get("phase"),
        "result": score.get("victor"),
        "attacker_score": score.get("attacker_score"),
        "defender_score": score.get("defender_score"),
    }
