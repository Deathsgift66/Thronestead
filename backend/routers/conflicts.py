# Project Name: Thronestead©
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


# ----------------------------
# New Endpoints for Conflict Tracker
# ----------------------------

@router.get("/all")
def list_all_conflicts(
    user_id: str = Depends(verify_jwt_token),
    db: Session = Depends(get_db),
) -> dict:
    """Return all wars with alliance names and metadata."""
    rows = db.execute(
        text(
            """
            SELECT w.war_id, a1.name AS alliance_a_name, a2.name AS alliance_b_name,
                   w.war_type, w.start_date, wt.phase, wt.castle_hp, wt.battle_tick,
                   ws.attacker_score, ws.defender_score, ws.victor
            FROM wars w
            JOIN wars_tactical wt ON w.war_id = wt.war_id
            LEFT JOIN war_scores ws ON ws.war_id = wt.war_id
            LEFT JOIN kingdoms k1 ON wt.attacker_kingdom_id = k1.kingdom_id
            LEFT JOIN kingdoms k2 ON wt.defender_kingdom_id = k2.kingdom_id
            LEFT JOIN alliances a1 ON k1.alliance_id = a1.alliance_id
            LEFT JOIN alliances a2 ON k2.alliance_id = a2.alliance_id
            ORDER BY w.start_date DESC
            """
        )
    ).fetchall()

    return {"wars": [dict(r._mapping) for r in rows]}


@router.get("/{war_id}")
def get_conflict_details(
    war_id: int,
    user_id: str = Depends(verify_jwt_token),
    db: Session = Depends(get_db),
) -> dict:
    """Fetch detailed information for a single war."""
    row = db.execute(
        text(
            """
            SELECT w.war_id, a1.name AS alliance_a_name, a2.name AS alliance_b_name,
                   w.war_type, w.start_date, wt.phase, wt.castle_hp, wt.battle_tick,
                   ws.attacker_score, ws.defender_score, ws.victor
            FROM wars w
            JOIN wars_tactical wt ON w.war_id = wt.war_id
            LEFT JOIN war_scores ws ON ws.war_id = wt.war_id
            LEFT JOIN kingdoms k1 ON wt.attacker_kingdom_id = k1.kingdom_id
            LEFT JOIN kingdoms k2 ON wt.defender_kingdom_id = k2.kingdom_id
            LEFT JOIN alliances a1 ON k1.alliance_id = a1.alliance_id
            LEFT JOIN alliances a2 ON k2.alliance_id = a2.alliance_id
            WHERE w.war_id = :wid
            """
        ),
        {"wid": war_id},
    ).fetchone()

    if not row:
        raise HTTPException(status_code=404, detail="War not found")

    logs = db.execute(
        text(
            """
            SELECT tick_number, event_type, damage_dealt, notes
            FROM combat_logs
            WHERE war_id = :wid
            ORDER BY tick_number
            """
        ),
        {"wid": war_id},
    ).fetchall()

    return {
        "war": dict(row._mapping),
        "logs": [dict(l._mapping) for l in logs],
    }


@router.get("/search")
def search_conflicts(
    q: str,
    user_id: str = Depends(verify_jwt_token),
    db: Session = Depends(get_db),
) -> dict:
    """Search conflicts by kingdom or alliance name."""
    search = f"%{q.lower()}%"
    rows = db.execute(
        text(
            """
            SELECT w.war_id, a1.name AS alliance_a_name, a2.name AS alliance_b_name,
                   w.war_type, w.start_date, wt.phase, wt.castle_hp, wt.battle_tick,
                   ws.attacker_score, ws.defender_score, ws.victor
            FROM wars w
            JOIN wars_tactical wt ON w.war_id = wt.war_id
            LEFT JOIN war_scores ws ON ws.war_id = wt.war_id
            LEFT JOIN kingdoms k1 ON wt.attacker_kingdom_id = k1.kingdom_id
            LEFT JOIN kingdoms k2 ON wt.defender_kingdom_id = k2.kingdom_id
            LEFT JOIN alliances a1 ON k1.alliance_id = a1.alliance_id
            LEFT JOIN alliances a2 ON k2.alliance_id = a2.alliance_id
            WHERE lower(a1.name) LIKE :s
               OR lower(a2.name) LIKE :s
               OR lower(k1.kingdom_name) LIKE :s
               OR lower(k2.kingdom_name) LIKE :s
            ORDER BY w.start_date DESC
            """
        ),
        {"s": search},
    ).fetchall()

    return {"wars": [dict(r._mapping) for r in rows]}


@router.post("/filter")
def filter_conflicts(
    payload: dict,
    user_id: str = Depends(verify_jwt_token),
    db: Session = Depends(get_db),
) -> dict:
    """Filter conflicts by phase status."""
    phase = payload.get("status")
    if phase not in {"active", "planning", "resolution", "concluded"}:
        raise HTTPException(status_code=400, detail="Invalid status")

    rows = db.execute(
        text(
            """
            SELECT w.war_id, a1.name AS alliance_a_name, a2.name AS alliance_b_name,
                   w.war_type, w.start_date, wt.phase, wt.castle_hp, wt.battle_tick,
                   ws.attacker_score, ws.defender_score, ws.victor
            FROM wars w
            JOIN wars_tactical wt ON w.war_id = wt.war_id
            LEFT JOIN war_scores ws ON ws.war_id = wt.war_id
            LEFT JOIN kingdoms k1 ON wt.attacker_kingdom_id = k1.kingdom_id
            LEFT JOIN kingdoms k2 ON wt.defender_kingdom_id = k2.kingdom_id
            LEFT JOIN alliances a1 ON k1.alliance_id = a1.alliance_id
            LEFT JOIN alliances a2 ON k2.alliance_id = a2.alliance_id
            WHERE wt.phase = :phase
            ORDER BY w.start_date DESC
            """
        ),
        {"phase": phase},
    ).fetchall()

    return {"wars": [dict(r._mapping) for r in rows]}
