# Project Name: Thronestead©
# File Name: alliance_project_service.py
# Version:  7/1/2025 10:38
# Developer: Deathsgift66

"""Service functions for managing alliance-wide projects."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timedelta

from fastapi import HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


# ------------------------------------------------------------------------------
# Project Management Logic
# ------------------------------------------------------------------------------


def list_available_projects(db: Session) -> list[dict]:
    """Return all projects that alliances can start (from catalogue)."""
    rows = db.execute(
        text(
            "SELECT * FROM project_alliance_catalogue WHERE is_active = true ORDER BY project_name"
        )
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

            SELECT pa.project_id, pc.project_name, pa.project_key, pa.started_at,
                   pa.expected_end, pa.contributed, pa.total_required,
                   pa.build_state
              FROM projects_alliance pa
              JOIN project_alliance_catalogue pc ON pa.project_key = pc.project_key
             WHERE pa.alliance_id = :aid AND pa.build_state = 'building'
             ORDER BY pa.started_at DESC

            """,
            {"aid": alliance_id},
        ),
        "completed": q(
            """

            SELECT pa.project_id, pc.project_name, pa.project_key, pa.started_at,
                   pa.expected_end, pa.completed_at, pa.contributed
              FROM projects_alliance pa
              JOIN project_alliance_catalogue pc ON pa.project_key = pc.project_key
             WHERE pa.alliance_id = :aid AND pa.build_state = 'completed'
             ORDER BY pa.completed_at DESC

            """,
            {"aid": alliance_id},
        ),
        "queued": q(
            """
            SELECT * FROM projects_alliance_in_progress
             WHERE alliance_id = :aid AND status = 'building'
             ORDER BY started_at
            """,
            {"aid": alliance_id},
        ),
    }


def start_alliance_project(
    db: Session, alliance_id: int, project_key: str, initiated_by: str
) -> datetime:
    """Initiate a new alliance project if it's valid and not already active."""
    row = db.execute(
        text(
            "SELECT build_time_seconds, resource_costs FROM project_alliance_catalogue "
            "WHERE project_key = :key AND is_active = true"
        ),
        {"key": project_key},
    ).fetchone()

    if not row:
        raise HTTPException(status_code=404, detail="Invalid or inactive project code")

    build_seconds, requirements = row
    ends_at = datetime.utcnow() + timedelta(seconds=build_seconds or 0)

    exists = db.execute(
        text(
            "SELECT 1 FROM projects_alliance WHERE alliance_id = :aid AND project_key = :key"
        ),
        {"aid": alliance_id, "key": project_key},
    ).fetchone()

    if exists:
        raise HTTPException(
            status_code=409, detail="Project already exists for this alliance"
        )

    active = db.execute(
        text(
            "SELECT 1 FROM projects_alliance_in_progress WHERE alliance_id = :aid AND project_key = :key AND status = 'building'"
        ),
        {"aid": alliance_id, "key": project_key},
    ).fetchone()
    if active:
        raise HTTPException(status_code=409, detail="Project already building")
    db.execute(
        text(
            """

            INSERT INTO projects_alliance (
                alliance_id, project_key, started_at,
                expected_end, contributed, total_required,
                build_state, initiated_by
            ) VALUES (
                :aid, :key, now(), :end, 0,
                :req, 'building', :uid

            )
        """
        ),
        {
            "aid": alliance_id,
            "key": project_key,
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
    project_key: str,
    user_id: str,
    amount: int,
) -> None:
    """Contribute to an ongoing alliance project."""
    row = db.execute(
        text(
            """

            SELECT project_id, contributed, total_required
            FROM projects_alliance
            WHERE alliance_id = :aid AND project_key = :key
              AND build_state = 'building'

            """
        ),
        {"aid": alliance_id, "key": project_key},
    ).fetchone()

    if not row:
        raise HTTPException(status_code=404, detail="Active project not found")

    pid, current = row
    new_total = min(current + amount, 100)

    db.execute(
        text(
            "UPDATE projects_alliance_in_progress SET progress = :val WHERE progress_id = :pid"
        ),
        {"val": new_total, "pid": pid},
    )

    db.execute(
        text(
            """
            INSERT INTO project_alliance_contributions (
                alliance_id, player_name, resource_type, amount, project_key, user_id
            ) VALUES (
                :aid, (SELECT username FROM users WHERE user_id = :uid), :rtype, :amt, :key, :uid
            )
            """
        ),
        {
            "aid": alliance_id,
            "uid": user_id,
            "rtype": "resource",
            "amt": amount,
            "key": project_key,
        },
    )

    db.commit()


def complete_project_if_ready(db: Session, alliance_id: int, project_key: str) -> bool:
    """Manually check if a project has met requirements and complete it."""
    row = db.execute(
        text(
            """
            SELECT project_id, contributed, total_required
            FROM projects_alliance
            WHERE alliance_id = :aid AND project_key = :key
              AND build_state = 'building'

            """
        ),
        {"aid": alliance_id, "key": project_key},
    ).fetchone()

    if not row:
        return False

    pid, progress, started_at, expected_end, built_by = row
    if progress < 100:
        return False

    db.execute(
        text(
            """
            INSERT INTO projects_alliance (
                alliance_id, name, progress, project_key, start_time, end_time,
                is_active, build_state, built_by, last_updated
            )
            SELECT :aid, c.project_name, 100, ip.project_key, ip.started_at, ip.expected_end,
                   true, 'completed', ip.built_by, now()
              FROM project_alliance_catalogue c
              JOIN projects_alliance_in_progress ip ON ip.progress_id = :pid
            """
        ),
        {"aid": alliance_id, "pid": pid},
    )
    db.execute(
        text(
            "UPDATE projects_alliance_in_progress SET status = 'completed' WHERE progress_id = :pid"
        ),
        {"pid": pid},
    )
    db.commit()
    return True


def get_project_modifiers(db: Session, alliance_id: int) -> dict:
    """Return cumulative modifiers from all completed alliance projects."""
    rows = db.execute(
        text(
            """
            SELECT pa.active_bonus
              FROM projects_alliance pa
               JOIN project_alliance_catalogue pc ON pa.project_key = pc.project_key

             WHERE pa.alliance_id = :aid AND pa.build_state = 'completed'
            """
        ),
        {"aid": alliance_id},
    ).fetchall()

    combined = {}
    for (mods,) in rows:
        if not mods:
            continue
        try:
            data = json.loads(mods)
        except Exception:
            continue
        if isinstance(data, dict):
            for category, values in data.items():
                combined.setdefault(category, {})
                for k, v in values.items():
                    combined[category][k] = combined[category].get(k, 0) + v
    return combined
