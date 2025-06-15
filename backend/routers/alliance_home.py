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
    Includes: core info, members, vault, projects, quests, wars, treaties, and activity logs.
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
    # 🏗️ Active Projects
    # --------------------
    projects = db.execute(
        text(
            """
            SELECT p.progress_id, c.project_name, p.project_key, p.progress, p.status
            FROM projects_alliance_in_progress p
            JOIN project_alliance_catalogue c ON p.project_key = c.project_key
            WHERE p.alliance_id = :aid
            ORDER BY p.started_at DESC
        """
        ),
        {"aid": aid},
    ).fetchall()
    projects = [
        {
            "progress_id": r[0],
            "name": r[1],
            "project_key": r[2],
            "progress": r[3],
            "status": r[4],
        }
        for r in projects
    ]

    # --------------------
    # 📘 Active Quests
    # --------------------
    quests = db.execute(
        text("""
            SELECT t.quest_code, q.name, q.description, t.status, t.progress, t.ends_at
            FROM quest_alliance_tracking t
            JOIN quest_alliance_catalogue q ON t.quest_code = q.quest_code
            WHERE t.alliance_id = :aid
            ORDER BY t.started_at DESC
        """),
        {"aid": aid},
    ).fetchall()
    quests = [
        {
            "quest_code": r[0],
            "name": r[1],
            "description": r[2],
            "status": r[3],
            "progress": r[4],
            "ends_at": r[5].isoformat() if r[5] else None,
        }
        for r in quests
    ]

    # --------------------
    # ⚔️ Active Wars
    # --------------------
    wars = db.execute(
        text("""
            SELECT w.alliance_war_id, w.attacker_alliance_id, w.defender_alliance_id,
                   w.war_status, s.attacker_score, s.defender_score, s.victor
            FROM alliance_wars w
            LEFT JOIN alliance_war_scores s ON w.alliance_war_id = s.alliance_war_id
            WHERE w.attacker_alliance_id = :aid OR w.defender_alliance_id = :aid
            ORDER BY w.start_date DESC
        """),
        {"aid": aid},
    ).fetchall()
    wars = [
        {
            "alliance_war_id": r[0],
            "attacker_alliance_id": r[1],
            "defender_alliance_id": r[2],
            "war_status": r[3],
            "attacker_score": r[4],
            "defender_score": r[5],
            "victor": r[6],
        }
        for r in wars
    ]

    # --------------------
    # 📜 Treaties
    # --------------------
    treaties = db.execute(
        text("""
            SELECT treaty_id, treaty_type, partner_alliance_id, status, signed_at
            FROM alliance_treaties
            WHERE alliance_id = :aid OR partner_alliance_id = :aid
            ORDER BY signed_at DESC
        """),
        {"aid": aid},
    ).fetchall()
    treaties = [
        {
            "treaty_id": r[0],
            "treaty_type": r[1],
            "partner_alliance_id": r[2],
            "status": r[3],
            "signed_at": r[4].isoformat() if r[4] else None,
        }
        for r in treaties
    ]


    # --------------------
    # 📅 Recent Activity
    # --------------------
    activity = db.execute(
        text("""
            SELECT l.description, u.username, l.created_at
            FROM alliance_activity_log l
            JOIN users u ON l.user_id = u.user_id
            WHERE l.alliance_id = :aid
            ORDER BY l.created_at DESC
            LIMIT 10
        """),
        {"aid": aid},
    ).fetchall()
    activity = [
        {
            "description": r[0],
            "username": r[1],
            "created_at": r[2].isoformat() if r[2] else None,
        }
        for r in activity
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
        "projects": projects,
        "quests": quests,
        "wars": wars,
        "treaties": treaties,
        "activity": activity,
    }
