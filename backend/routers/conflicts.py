# Project Name: Kingmakers Rise©
# File Name: conflicts.py
# Version 6.13.2025.19.49
# Developer: Deathsgift66

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from ..database import get_db
from ..security import verify_jwt_token
from .progression_router import get_kingdom_id
from ..supabase_client import get_supabase_client

router = APIRouter(prefix="/api/conflicts", tags=["conflicts"])

# ----------------------------
# Helper
# ----------------------------

def get_alliance_id(db: Session, user_id: str) -> int:
    """Fetch alliance ID for the user."""
    row = db.execute(
        text("SELECT alliance_id FROM users WHERE user_id = :uid"),
        {"uid": user_id},
    ).fetchone()
    if not row or not row[0]:
        raise HTTPException(status_code=404, detail="Alliance not found")
    return row[0]

# ----------------------------
# Endpoints
# ----------------------------

@router.get("/kingdom")
def list_kingdom_wars(
    user_id: str = Depends(verify_jwt_token),
    db: Session = Depends(get_db),
):
    """Return list of wars involving the user's kingdom."""
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
    """Return list of wars involving the user's alliance."""
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
    """Return full summary of a war the user is a participant in."""
    kid = get_kingdom_id(db, user_id)
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

@router.get("/overview")
def list_conflict_overview(
    user_id: str = Depends(verify_jwt_token),
    db: Session = Depends(get_db),
) -> dict:
    """Return a detailed overview of all wars (tactical+strategic)."""
    rows = db.execute(
        text(
            """
            SELECT wt.war_id, w.war_type, wt.phase, wt.battle_tick, wt.castle_hp,
                   wt.started_at,
                   k1.kingdom_name AS attacker_kingdom,
                   k2.kingdom_name AS defender_kingdom,
                   a1.name AS attacker_alliance,
                   a2.name AS defender_alliance,
                   ws.victor,
                   ws.attacker_score,
                   ws.defender_score,
                   br.winner_side
            FROM wars_tactical wt
            JOIN wars w ON wt.war_id = w.war_id
            LEFT JOIN war_scores ws ON ws.war_id = wt.war_id
            LEFT JOIN battle_resolution_logs br ON br.war_id = wt.war_id
            LEFT JOIN kingdoms k1 ON wt.attacker_kingdom_id = k1.kingdom_id
            LEFT JOIN kingdoms k2 ON wt.defender_kingdom_id = k2.kingdom_id
            LEFT JOIN alliances a1 ON k1.alliance_id = a1.alliance_id
            LEFT JOIN alliances a2 ON k2.alliance_id = a2.alliance_id
            ORDER BY wt.started_at DESC
            """
        )
    ).fetchall()

    return {"wars": [dict(r._mapping) for r in rows]}
