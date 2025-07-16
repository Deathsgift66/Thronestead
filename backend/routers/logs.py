# Project Name: Thronestead©
# File Name: logs.py
# Version: 1.0
# Developer: Production Audit
"""API routes for logging client errors such as 404 hits."""

from fastapi import APIRouter
from pydantic import BaseModel
from html import escape

from ..supabase_client import get_supabase_client

router = APIRouter(prefix="/api/logs", tags=["logs"])


class ErrorPayload(BaseModel):
    path: str | None = None
    referrer: str | None = None
    user_agent: str | None = None
    type: str


@router.post("/404")
def log_404(payload: ErrorPayload):
    """Record 404 or runtime error events from the client."""
    supabase = get_supabase_client()
    ua = escape(payload.user_agent or "")[:255]
    record = {
        "path": payload.path,
        "referrer": payload.referrer,
        "user_agent": ua,
        "type": payload.type,
    }
    supabase.table("client_errors").insert(record).execute()
    return {"status": "logged"}
