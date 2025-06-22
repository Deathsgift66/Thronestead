"""Account settings management routes for Thronestead."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.orm import Session

from ..database import get_db
from ..security import verify_jwt_token
from services.audit_service import log_action


router = APIRouter(prefix="/api/account", tags=["account"])
alt_router = APIRouter(prefix="/api/user", tags=["account"])


try:
    templates = Jinja2Templates(directory=Path(__file__).resolve().parents[2])
except Exception:  # pragma: no cover - fallback for missing jinja2
    class _DummyTemplates:
        def __init__(self, directory: Path):
            self.directory = directory

        def TemplateResponse(self, name: str, context: dict) -> HTMLResponse:
            html = (self.directory / name).read_text(encoding="utf-8")
            response = HTMLResponse(content=html)
            setattr(response, "context", context)
            return response

    templates = _DummyTemplates(Path(__file__).resolve().parents[2])


class UpdatePayload(BaseModel):
    """Incoming data for updating account profile details."""

    display_name: str | None = None
    motto: str | None = None
    bio: str | None = None
    profile_picture_url: str | None = None
    theme_preference: str | None = None
    profile_banner: str | None = None
    ip_login_alerts: bool | None = None
    email_login_confirmations: bool | None = None


class SessionPayload(BaseModel):
    session_id: str


class SessionInfo(BaseModel):
    session_id: str
    device: str
    last_seen: datetime | None = None


class UserProfile(BaseModel):
    username: str | None = None
    display_name: str | None = None
    profile_picture_url: str | None = None
    email: str | None = None
    region: str | None = None
    kingdom_name: str | None = None
    alliance_name: str | None = None
    motto: str | None = None
    bio: str | None = None
    theme_preference: str | None = None
    profile_banner: str | None = None
    vip_level: int | None = None
    founder: bool | None = None
    expires_at: datetime | None = None
    ip_login_alerts: bool | None = None
    email_login_confirmations: bool | None = None
    sessions: list[SessionInfo] = Field(default_factory=list)


@router.get("/profile", response_class=HTMLResponse, response_model=None)
def profile(request: Request):
    """Serve the user's profile settings page."""

    return templates.TemplateResponse("profile.html", {"request": request})


@router.post("/update", response_model=None)
def update_profile(
    payload: UpdatePayload,
    user_id: str = Depends(verify_jwt_token),
    db: Session = Depends(get_db),
):
    """Apply updates to a user's profile and customization settings."""

    current = db.execute(
        text("SELECT display_name, profile_picture_url FROM users WHERE user_id = :uid"),
        {"uid": user_id},
    ).fetchone()

    settings_rows = db.execute(
        text(
            "SELECT setting_key, setting_value FROM user_setting_entries "
            "WHERE user_id = :uid AND setting_key IN ('ip_login_alerts','email_login_confirmations')"
        ),
        {"uid": user_id},
    ).fetchall()
    settings_current = {r[0]: r[1] for r in settings_rows}

    customization = db.execute(
        text(
            "SELECT motto, bio, theme_preference, profile_banner FROM user_customization WHERE user_id = :uid"
        ),
        {"uid": user_id},
    ).fetchone()

    db.execute(
        text("UPDATE users SET display_name = :dn, profile_picture_url = :pic WHERE user_id = :uid"),
        {"dn": payload.display_name, "pic": payload.profile_picture_url, "uid": user_id},
    )

    if payload.ip_login_alerts is not None:
        db.execute(
            text(
                "INSERT INTO user_setting_entries (user_id, setting_key, setting_value) "
                "VALUES (:uid, 'ip_login_alerts', :val) "
                "ON CONFLICT (user_id, setting_key) DO UPDATE SET setting_value = EXCLUDED.setting_value"
            ),
            {"uid": user_id, "val": str(payload.ip_login_alerts).lower()},
        )
    if payload.email_login_confirmations is not None:
        db.execute(
            text(
                "INSERT INTO user_setting_entries (user_id, setting_key, setting_value) "
                "VALUES (:uid, 'email_login_confirmations', :val) "
                "ON CONFLICT (user_id, setting_key) DO UPDATE SET setting_value = EXCLUDED.setting_value"
            ),
            {"uid": user_id, "val": str(payload.email_login_confirmations).lower()},
        )

    db.execute(
        text(
            """
            INSERT INTO user_customization (user_id, motto, bio, theme_preference, profile_banner)
            VALUES (:uid, :motto, :bio, :theme, :banner)
            ON CONFLICT (user_id) DO UPDATE SET
                motto = EXCLUDED.motto,
                bio = EXCLUDED.bio,
                theme_preference = EXCLUDED.theme_preference,
                profile_banner = EXCLUDED.profile_banner
            """
        ),
        {
            "uid": user_id,
            "motto": payload.motto,
            "bio": payload.bio,
            "theme": payload.theme_preference,
            "banner": payload.profile_banner,
        },
    )
    db.commit()

    diffs: dict[str, object] = {}
    if current:
        if payload.display_name != current[0]:
            diffs["display_name"] = payload.display_name
        if payload.profile_picture_url != current[1]:
            diffs["profile_picture_url"] = payload.profile_picture_url
        if (
            payload.ip_login_alerts is not None
            and payload.ip_login_alerts != (settings_current.get("ip_login_alerts") == "true")
        ):
            diffs["ip_login_alerts"] = payload.ip_login_alerts
        if (
            payload.email_login_confirmations is not None
            and payload.email_login_confirmations
            != (settings_current.get("email_login_confirmations") == "true")
        ):
            diffs["email_login_confirmations"] = payload.email_login_confirmations
    if customization:
        if payload.motto != customization[0]:
            diffs["motto"] = payload.motto
        if payload.bio != customization[1]:
            diffs["bio"] = payload.bio
        if payload.theme_preference != customization[2]:
            diffs["theme_preference"] = payload.theme_preference
        if payload.profile_banner != customization[3]:
            diffs["profile_banner"] = payload.profile_banner

    log_action(db, user_id, "update_profile", str(diffs))
    return {"message": "updated"}


@router.post("/logout-session", response_model=None)
def logout_session(
    payload: SessionPayload,
    user_id: str = Depends(verify_jwt_token),
    db: Session = Depends(get_db),
):
    """Revoke an active session for the authenticated user."""

    row = db.execute(
        text(
            "SELECT session_id FROM user_active_sessions WHERE session_id = :sid AND user_id = :uid"
        ),
        {"sid": payload.session_id, "uid": user_id},
    ).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Session not found")

    db.execute(
        text("UPDATE user_active_sessions SET session_status = 'revoked' WHERE session_id = :sid"),
        {"sid": payload.session_id},
    )
    db.commit()
    log_action(db, user_id, "logout_session", payload.session_id)
    return {"message": "session revoked"}


@alt_router.get("/settings", response_model=None)
def get_user_settings(
    user_id: str = Depends(verify_jwt_token),
    db: Session = Depends(get_db),
):
    """Return all user setting entries as a key-value map."""

    rows = db.execute(
        text("SELECT setting_key, setting_value FROM user_setting_entries WHERE user_id = :uid"),
        {"uid": user_id},
    ).fetchall()
    return {r[0]: r[1] for r in rows}


@alt_router.post("/settings", response_model=None)
def update_user_settings(
    settings: dict,
    user_id: str = Depends(verify_jwt_token),
    db: Session = Depends(get_db),
):
    """Insert or update arbitrary user setting entries."""

    for key, value in settings.items():
        db.execute(
            text(
                """
                INSERT INTO user_setting_entries (user_id, setting_key, setting_value)
                VALUES (:uid, :key, :val)
                ON CONFLICT (user_id, setting_key)
                DO UPDATE SET setting_value = EXCLUDED.setting_value
                """
            ),
            {"uid": user_id, "key": key, "val": value},
        )
    db.commit()
    return {"status": "updated"}
