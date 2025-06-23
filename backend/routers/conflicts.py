# Project Name: Thronestead©
# File Name: conflicts.py
# Version 6.13.2025.19.49
# Developer: Deathsgift66

"""
Project: Thronestead ©
File: conflicts.py
Role: API routes for conflicts.
Version: 2025-06-21
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from ..database import get_db
from ..security import require_user_id
from ..supabase_client import get_supabase_client
from .progression_router import get_kingdom_id

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
    user_id: str = Depends(require_user_id),
    db: Session = Depends(get_db),
):
    """Return wars involving the player's kingdom."""
    kid = get_kingdom_id(db, user_id)
    supabase = get_supabase_client()
    res = (
        supabase.table("wars")
        .select("war_id,attacker_kingdom_id,defender_kingdom_id,attacker_name,defender_name")
        .or_(f"attacker_kingdom_id.eq.{kid},defender_kingdom_id.eq.{kid}")
        .execute()
    )
    wars = getattr(res, "data", res) or []
    return {"wars": wars}


@router.get("/details")
def get_war_details(
    war_id: int,
    user_id: str = Depends(require_user_id),
    db: Session = Depends(get_db),
):
    """Return full war details if the user is a participant."""
    kid = get_kingdom_id(db, user_id)
    supabase = get_supabase_client()

    war_res = (
        supabase.table("wars").select("*").eq("war_id", war_id).single().execute()
    )
    war = getattr(war_res, "data", None)
    if not war:
        raise HTTPException(status_code=404, detail="War not found")
    if war.get("attacker_kingdom_id") != kid and war.get("defender_kingdom_id") != kid:
        raise HTTPException(status_code=403, detail="Access denied")

    score_res = (
        supabase.table("war_scores").select("*").eq("war_id", war_id).single().execute()
    )
    score = getattr(score_res, "data", score_res) or {}
    war.update(score)
    return {"war": war}


@router.get("/overview")
def list_conflict_overview(
    user_id: str = Depends(require_user_id),
    db: Session = Depends(get_db),
):
    """Return a tactical overview of wars involving the player's kingdom."""
    kid = get_kingdom_id(db, user_id)
    rows = db.execute(
        text(
            """
            SELECT wt.war_id, w.war_type, wt.phase, wt.battle_tick,
                   wt.tick_interval_seconds, w.start_date,
                   w.attacker_name, w.defender_name,
                   aa.name AS attacker_alliance, da.name AS defender_alliance,
                   wt.terrain_id, wt.attacker_kingdom_id, wt.defender_kingdom_id,
                   wt.current_turn
            FROM wars_tactical wt
            JOIN wars w ON w.war_id = wt.war_id
            LEFT JOIN alliances aa ON w.attacker_alliance_id = aa.alliance_id
            LEFT JOIN alliances da ON w.defender_alliance_id = da.alliance_id
            WHERE wt.attacker_kingdom_id = :kid OR wt.defender_kingdom_id = :kid
            ORDER BY w.start_date DESC
            """
        ),
        {"kid": kid},
    ).fetchall()

    wars = [
        {
            "war_id": r[0],
            "war_type": r[1],
            "phase": r[2],
            "battle_tick": r[3],
            "tick_interval_seconds": r[4],
            "start_date": r[5],
            "attacker_name": r[6],
            "defender_name": r[7],
            "attacker_alliance": r[8],
            "defender_alliance": r[9],
            "terrain_id": r[10],
            "attacker_kingdom_id": r[11],
            "defender_kingdom_id": r[12],
            "current_turn": r[13],
        }
        for r in rows
    ]
    return {"wars": wars}


@router.get("/all")
def list_all_conflicts(
    user_id: str = Depends(require_user_id),
    db: Session = Depends(get_db),
):
    """Return all wars involving the player's alliance."""
    aid = get_alliance_id(db, user_id)
    rows = db.execute(
        text(
            """
            SELECT wt.war_id, aa.name AS attacker_alliance, da.name AS defender_alliance,
                   w.war_type, w.start_date, wt.war_status, wt.tick_interval_seconds,
                   wt.attacker_kingdom_id, wt.defender_kingdom_id, wt.current_turn
            FROM wars_tactical wt
            JOIN wars w ON wt.war_id = w.war_id
            LEFT JOIN alliances aa ON w.attacker_alliance_id = aa.alliance_id
            LEFT JOIN alliances da ON w.defender_alliance_id = da.alliance_id
            WHERE w.attacker_alliance_id = :aid OR w.defender_alliance_id = :aid
            ORDER BY w.start_date DESC
            """
        ),
        {"aid": aid},
    ).fetchall()

    wars = [
        {
            "war_id": r[0],
            "attacker_alliance": r[1],
            "defender_alliance": r[2],
            "war_type": r[3],
            "start_date": r[4],
            "war_status": r[5],
            "tick_interval_seconds": r[6],
            "attacker_kingdom_id": r[7],
            "defender_kingdom_id": r[8],
            "current_turn": r[9],
        }
        for r in rows
    ]
    return {"wars": wars}


@router.get("/view")
def get_conflict_details(
    war_id: int,
    user_id: str = Depends(require_user_id),
    db: Session = Depends(get_db),
):
    """Return detailed information about a specific war."""
    rows = db.execute(
        text(
            """
            SELECT wt.war_id, aa.name AS attacker_alliance, da.name AS defender_alliance,
                   w.war_type, w.start_date, wt.war_status, wt.tick_interval_seconds,
                   wt.attacker_kingdom_id, wt.defender_kingdom_id, wt.current_turn
            FROM wars_tactical wt
            JOIN wars w ON wt.war_id = w.war_id
            LEFT JOIN alliances aa ON w.attacker_alliance_id = aa.alliance_id
            LEFT JOIN alliances da ON w.defender_alliance_id = da.alliance_id
            WHERE wt.war_id = :wid
            """
        ),
        {"wid": war_id},
    ).fetchall()
    if not rows:
        raise HTTPException(status_code=404, detail="War not found")
    r = rows[0]
    war = {
        "war_id": r[0],
        "attacker_alliance": r[1],
        "defender_alliance": r[2],
        "war_type": r[3],
        "start_date": r[4],
        "war_status": r[5],
        "tick_interval_seconds": r[6],
        "attacker_kingdom_id": r[7],
        "defender_kingdom_id": r[8],
        "current_turn": r[9],
    }
    return {"war": war}


@router.get("/search")
def search_conflicts(
    q: str,
    user_id: str = Depends(require_user_id),
    db: Session = Depends(get_db),
):
    """Search wars by alliance names."""
    aid = get_alliance_id(db, user_id)
    rows = db.execute(
        text(
            """
            SELECT wt.war_id, aa.name AS attacker_alliance, da.name AS defender_alliance,
                   w.war_type, w.start_date, wt.war_status, wt.tick_interval_seconds,
                   wt.attacker_kingdom_id, wt.defender_kingdom_id, wt.current_turn
            FROM wars_tactical wt
            JOIN wars w ON wt.war_id = w.war_id
            LEFT JOIN alliances aa ON w.attacker_alliance_id = aa.alliance_id
            LEFT JOIN alliances da ON w.defender_alliance_id = da.alliance_id
            WHERE (aa.name ILIKE :s OR da.name ILIKE :s)
              AND (w.attacker_alliance_id = :aid OR w.defender_alliance_id = :aid)
            ORDER BY w.start_date DESC
            """
        ),
        {"s": f"%{q}%", "aid": aid},
    ).fetchall()

    wars = [
        {
            "war_id": r[0],
            "attacker_alliance": r[1],
            "defender_alliance": r[2],
            "war_type": r[3],
            "start_date": r[4],
            "war_status": r[5],
            "tick_interval_seconds": r[6],
            "attacker_kingdom_id": r[7],
            "defender_kingdom_id": r[8],
            "current_turn": r[9],
        }
        for r in rows
    ]
    return {"wars": wars}


@router.get("/filter")
def filter_conflicts(
    filters: dict,
    user_id: str = Depends(require_user_id),
    db: Session = Depends(get_db),
):
    """Filter wars based on status/phase."""
    phase = filters.get("status")
    rows = db.execute(
        text("SELECT war_id FROM wars_tactical WHERE phase = :phase"),
        {"phase": phase},
    ).fetchall()
    wars = [{"war_id": r[0]} for r in rows]
    return {"wars": wars}

