# Project Name: Kingmakers Rise©
# File Name: alliance_project_service.py
# Version: 6.13.2025.19.49
# Developer: Deathsgift66

"""Service functions for managing alliance-wide projects."""

from __future__ import annotations
from typing import Optional
from datetime import datetime, timedelta

from fastapi import HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session
import logging

logger = logging.getLogger(__name__)


# ------------------------------------------------------------------------------
# Project Management Logic
# ------------------------------------------------------------------------------

def list_available_projects(db: Session) -> list[dict]:
    """Return all projects that alliances can start (from catalogue)."""
    rows = db.execute(
        text("SELECT * FROM project_alliance_catalogue WHERE is_active = true ORDER BY tier, name")
    ).fetchall()
    return [dict(r._mapping) for r in rows]


def list_alliance_projects(db: Session, alliance_id: int) -> dict:
    """Return completed, active, and queued projects for an alliance."""
    def q(query: str, params: dict) -> list[dict]:
        rows = db.execute(text(query), params).fetchall()
        return [dict(r._mapping) for r in rows]

    return {
        "active": q(
            """
            SELECT pa.project_id, pc.name, pa.project_code, pa.started_at,
                   pa.expected_end, pa.contributed, pa.total_required,
                   pa.build_state
              FROM projects_alliance pa
              JOIN project_alliance_catalogue pc ON pa.project_code = pc.project_code
             WHERE pa.alliance_id = :aid AND pa.build_state = 'in_progress'
             ORDER BY pa.started_at DESC
            """,
            {"aid": alliance_id},
        ),
        "completed": q(
            """
            SELECT pa.project_id, pc.name, pa.project_code, pa.started_at,
                   pa.expected_end, pa.completed_at, pa.contributed
              FROM projects_alliance pa
              JOIN project_alliance_catalogue pc ON pa.project_code = pc.project_code
             WHERE pa.alliance_id = :aid AND pa.build_state = 'completed'
             ORDER BY pa.completed_at DESC
            """,
            {"aid": alliance_id},
        ),
        "queued": q(
            """
            SELECT * FROM projects_alliance_in_progress
             WHERE alliance_id = :aid AND status = 'building'
             ORDER BY starts_at
            """,
            {"aid": alliance_id},
        ),
    }


def start_alliance_project(
    db: Session, alliance_id: int, project_code: str, initiated_by: str
) -> datetime:
    """Initiate a new alliance project if it's valid and not already active."""
    # Validate project existence and get duration
    row = db.execute(
        text(
            "SELECT duration_hours, resource_requirements FROM project_alliance_catalogue "
            "WHERE project_code = :code AND is_active = true"
        ),
        {"code": project_code},
    ).fetchone()

    if not row:
        raise HTTPException(status_code=404, detail="Invalid or inactive project code")

    duration_hours, requirements = row
    ends_at = datetime.utcnow() + timedelta(hours=duration_hours or 0)

    # Prevent duplicates
    exists = db.execute(
        text(
            "SELECT 1 FROM projects_alliance WHERE alliance_id = :aid AND project_code = :code"
        ),
        {"aid": alliance_id, "code": project_code},
    ).fetchone()

    if exists:
        raise HTTPException(status_code=409, detail="Project already exists for this alliance")

    # Insert project into main table
    db.execute(
        text(
            """
            INSERT INTO projects_alliance (
                alliance_id, project_code, started_at,
                expected_end, contributed, total_required,
                build_state, initiated_by
            ) VALUES (
                :aid, :code, now(), :end, 0,
                :req, 'in_progress', :uid
            )
            """
        ),
        {
            "aid": alliance_id,
            "code": project_code,
            "end": ends_at,
            "req": sum((requirements or {}).values()),
            "uid": initiated_by,
        },
    )

    db.commit()
    return ends_at


def contribute_to_project(
    db: Session,
    alliance_id: int,
    project_code: str,
    user_id: str,
    amount: int,
) -> None:
    """Contribute to an ongoing alliance project."""
    # Fetch current project status
    row = db.execute(
        text(
            """
            SELECT project_id, contributed, total_required
            FROM projects_alliance
            WHERE alliance_id = :aid AND project_code = :code
              AND build_state = 'in_progress'
            """
        ),
        {"aid": alliance_id, "code": project_code},
    ).fetchone()

    if not row:
        raise HTTPException(status_code=404, detail="Active project not found")

    project_id, current, total = row
    new_total = min(current + amount, total)

    db.execute(
        text(
            "UPDATE projects_alliance SET contributed = :val, last_updated = now() WHERE project_id = :pid"
        ),
        {"val": new_total, "pid": project_id},
    )

    db.execute(
        text(
            """
            INSERT INTO project_contributions (
                project_id, user_id, amount, contributed_at
            ) VALUES (
                :pid, :uid, :amt, now()
            )
            """
        ),
        {"pid": project_id, "uid": user_id, "amt": amount},
    )

    db.commit()


def complete_project_if_ready(db: Session, alliance_id: int, project_code: str) -> bool:
    """Manually check if a project has met requirements and complete it."""
    row = db.execute(
        text(
            """
            SELECT project_id, contributed, total_required
            FROM projects_alliance
            WHERE alliance_id = :aid AND project_code = :code
              AND build_state = 'in_progress'
            """
        ),
        {"aid": alliance_id, "code": project_code},
    ).fetchone()

    if not row:
        return False

    project_id, contributed, required = row
    if contributed < required:
        return False

    db.execute(
        text(
            """
            UPDATE projects_alliance
            SET build_state = 'completed',
                completed_at = now(),
                last_updated = now()
            WHERE project_id = :pid
            """
        ),
        {"pid": project_id},
    )
    db.commit()
    return True


def get_project_modifiers(
    db: Session, alliance_id: int
) -> dict:
    """Return cumulative modifiers from all completed alliance projects."""
    rows = db.execute(
        text(
            """
            SELECT pc.modifiers
              FROM projects_alliance pa
              JOIN project_alliance_catalogue pc ON pa.project_code = pc.project_code
             WHERE pa.alliance_id = :aid AND pa.build_state = 'completed'
            """
        ),
        {"aid": alliance_id},
    ).fetchall()

    combined = {}
    for (mods,) in rows:
        if isinstance(mods, dict):
            for category, values in mods.items():
                combined.setdefault(category, {})
                for k, v in values.items():
                    combined[category][k] = combined[category].get(k, 0) + v
    return combined
