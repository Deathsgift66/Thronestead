# Project Name: Kingmakers Rise©
# File Name: alliance_home.py
# Version: 6.13.2025.19.49
# Developer: Deathsgift66

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text

from ..database import get_db
from ..security import require_user_id
from backend.models import User, Alliance, AllianceMember, AllianceVault

router = APIRouter(prefix="/api/alliance-home", tags=["alliance_home"])


@router.get("/details")
def alliance_details(
    user_id: str = Depends(require_user_id),
    db: Session = Depends(get_db),
):
    """
    Return full summary data for the user's current alliance.
    Includes: core info, members, vault, projects, quests, wars, treaties, achievements, and activity logs.
    """
    # --------------------
    # 🔐 Validate User & Alliance
    # --------------------
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user or not user.alliance_id:
        raise HTTPException(status_code=404, detail="Alliance not found")

    aid = user.alliance_id
    alliance = db.query(Alliance).filter(Alliance.alliance_id == aid).first()
    if not alliance:
        raise HTTPException(status_code=404, detail="Alliance data missing")

    # --------------------
    # 🧑 Members
    # --------------------
    member_rows = (
        db.query(AllianceMember, User.username, User.profile_picture_url)
        .join(User, AllianceMember.user_id == User.user_id)
        .filter(AllianceMember.alliance_id == aid)
        .order_by(AllianceMember.rank, AllianceMember.contribution.desc())
        .all()
    )
    members = [
        {
            "user_id": str(m.user_id),
            "username": username,
            "avatar": avatar,
            "rank": m.rank,
            "contribution": m.contribution,
            "status": m.status,
            "crest": m.crest,
        }
        for m, username, avatar in member_rows
    ]

    # --------------------
    # 💰 Vault
    # --------------------
    vault = db.query(AllianceVault).filter(AllianceVault.alliance_id == aid).first()
    vault_data = {
        k: getattr(vault, k)
        for k in vault.__table__.columns.keys()
        if k != "alliance_id"
    } if vault else {}


    # --------------------
    # ⚔️ Active Wars
    # --------------------
    wars = db.execute(
        text(
            "SELECT alliance_war_id, attacker_alliance_id, defender_alliance_id,"
            " phase, castle_hp, battle_tick, war_status, start_date, end_date "
            "FROM alliance_wars "
            "WHERE attacker_alliance_id = :aid OR defender_alliance_id = :aid "
            "ORDER BY start_date DESC"
        ),
        {"aid": aid},
    ).fetchall()
    wars = [
        {
            "alliance_war_id": r[0],
            "attacker_alliance_id": r[1],
            "defender_alliance_id": r[2],
            "phase": r[3],
            "castle_hp": r[4],
            "battle_tick": r[5],
            "war_status": r[6],
            "start_date": r[7].isoformat() if r[7] else None,
            "end_date": r[8].isoformat() if r[8] else None,
        }
        for r in wars
    ]


    # --------------------
    # 🏰 Final Alliance Info
    # --------------------
    alliance_info = {
        "alliance_id": alliance.alliance_id,
        "name": alliance.name,
        "leader": alliance.leader,
        "status": alliance.status,
        "region": alliance.region,
        "level": alliance.level,
        "motd": alliance.motd,
        "banner": alliance.banner,
        "created_at": alliance.created_at.isoformat() if alliance.created_at else None,
        "military_score": alliance.military_score,
        "economy_score": alliance.economy_score,
        "diplomacy_score": alliance.diplomacy_score,
        "wars_count": alliance.wars_count,
        "treaties_count": alliance.treaties_count,
        "projects_active": alliance.projects_active,
        "member_count": len(members),
    }

    return {
        "alliance": alliance_info,
        "members": members,
        "vault": vault_data,
        "wars": wars,
    }
    }
