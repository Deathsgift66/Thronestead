# Project Name: Thronestead©
# File Name: alliance_members_api.py
# Version 6.14.2025
# Developer: OpenAI Codex

"""Provides a detailed list of alliance members with score and output data."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from ..database import get_db
from ..security import require_user_id
from backend.models import (
    User,
    AllianceMember,
    AllianceRole,
    Kingdom,
    KingdomVillage,
    VillageProduction,
)

router = APIRouter(prefix="/api/alliance/members", tags=["alliance_members"])


@router.get("")
def list_members(
    sort_by: str = "username",
    direction: str = "asc",
    search: str = "",
    user_id: str = Depends(require_user_id),
    db: Session = Depends(get_db),
):
    """Return alliance members joined with kingdom scores and production output."""

    viewer = db.query(User).filter_by(user_id=user_id).first()
    if not viewer or not viewer.alliance_id:
        raise HTTPException(status_code=404, detail="Alliance not found")

    aid = viewer.alliance_id

    # 🏭 Output per kingdom via villages
    output_subquery = (
        db.query(
            Kingdom.user_id.label("uid"),
            func.coalesce(func.sum(VillageProduction.production_rate), 0).label("total_output"),
        )
        .join(KingdomVillage, KingdomVillage.kingdom_id == Kingdom.kingdom_id)
        .join(VillageProduction, VillageProduction.village_id == KingdomVillage.village_id)
        .group_by(Kingdom.user_id)
        .subquery()
    )

    query = (
        db.query(
            AllianceMember.user_id,
            AllianceMember.username,
            AllianceMember.rank,
            AllianceRole.role_name.label("role"),
            AllianceMember.status,
            AllianceMember.contribution,
            Kingdom.economy_score,
            Kingdom.military_score,
            Kingdom.diplomacy_score,
            func.coalesce(output_subquery.c.total_output, 0).label("total_output"),
            User.profile_picture_url.label("crest_url"),
        )
        .join(User, User.user_id == AllianceMember.user_id)
        .outerjoin(AllianceRole, AllianceMember.role_id == AllianceRole.role_id)
        .outerjoin(Kingdom, Kingdom.user_id == AllianceMember.user_id)
        .outerjoin(output_subquery, output_subquery.c.uid == AllianceMember.user_id)
        .filter(AllianceMember.alliance_id == aid)
    )

    if search.strip():
        query = query.filter(AllianceMember.username.ilike(f"%{search.strip()}%"))

    # 🔀 Sort Handling
    sort_map = {
        "username": AllianceMember.username,
        "rank": AllianceMember.rank,
        "contribution": AllianceMember.contribution,
        "status": AllianceMember.status,
        "military_score": Kingdom.military_score,
        "economy_score": Kingdom.economy_score,
        "diplomacy_score": Kingdom.diplomacy_score,
        "total_output": output_subquery.c.total_output,
    }
    sort_col = sort_map.get(sort_by, AllianceMember.username)
    order_clause = sort_col.desc() if direction.lower() == "desc" else sort_col.asc()
    query = query.order_by(order_clause)

    rows = query.all()

    return [
        {
            "user_id": str(r.user_id),
            "username": r.username,
            "rank": r.rank or "Member",
            "role": r.role or "Member",
            "status": r.status,
            "contribution": r.contribution or 0,
            "economy_score": r.economy_score or 0,
            "military_score": r.military_score or 0,
            "diplomacy_score": r.diplomacy_score or 0,
            "total_output": float(r.total_output or 0),
            "crest_url": r.crest_url,
        }
        for r in rows
    ]
