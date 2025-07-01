# Comment
# Project Name: Thronestead©
# File Name: reports.py
# Version: 7/1/2025 10:31
# Developer: Deathsgift66
"""
Project: Thronestead ©
File: reports.py
Role: API routes for submitting moderation reports.
Version: 2025-06-21
"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel, validator
from sqlalchemy.orm import Session

from services.moderation import validate_clean_text

from ..database import get_db
from ..models import UserReport
from ..security import verify_jwt_token

router = APIRouter(prefix="/api/reports", tags=["reports"])


class ReportPayload(BaseModel):
    category: str
    description: str
    target_id: str | None = None

    @validator("description")
    def clean_description(cls, v: str) -> str:  # noqa: D401
        """Validate report description for length and banned words."""
        validate_clean_text(v)
        if len(v) > 1000:
            raise ValueError("Description too long")
        return v.strip()


@router.post("/submit")
def submit_report(
    payload: ReportPayload,
    user_id: str = Depends(verify_jwt_token),
    db: Session = Depends(get_db),
):
    """Create a new user report for moderation review."""
    report = UserReport(
        reporter_id=user_id,
        target_id=payload.target_id,
        category=payload.category,
        description=payload.description,
    )
    db.add(report)
    db.commit()
    return {"status": "submitted", "report_id": report.report_id}


@router.get("/mine")
def list_reports(
    user_id: str = Depends(verify_jwt_token),
    db: Session = Depends(get_db),
):
    """Return reports submitted by the current user."""
    rows = (
        db.query(UserReport)
        .filter_by(reporter_id=user_id)
        .order_by(UserReport.report_id.desc())
        .all()
    )
    return {
        "reports": [
            {
                "report_id": r.report_id,
                "category": r.category,
                "description": r.description,
            }
            for r in rows
        ]
    }
