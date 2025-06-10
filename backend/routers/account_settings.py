from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session

from ..database import get_db
from ..security import verify_jwt_token
from services.audit_service import log_action

router = APIRouter(prefix="/api/account", tags=["account"])


class UpdatePayload(BaseModel):
    display_name: str | None = None
    motto: str | None = None
    bio: str | None = None
    profile_picture_url: str | None = None
    theme_preference: str | None = None
    profile_banner: str | None = None


class SessionPayload(BaseModel):
    session_id: str


@router.get("/profile")
def load_profile(
    user_id: str = Depends(verify_jwt_token),
    db: Session = Depends(get_db),
):
    row = db.execute(
        text(
            """
            SELECT u.username, u.display_name, u.profile_picture_url, u.email, u.region,
                   k.kingdom_name,
                   a.name AS alliance_name,
                   c.motto, c.bio, c.theme_preference, c.profile_banner,
                   v.vip_level, v.founder, v.expires_at
            FROM users u
            LEFT JOIN kingdoms k ON k.user_id = u.user_id
            LEFT JOIN alliances a ON a.alliance_id = u.alliance_id
            LEFT JOIN user_customization c ON c.user_id = u.user_id
            LEFT JOIN kingdom_vip_status v ON v.user_id = u.user_id
            WHERE u.user_id = :uid
            """
        ),
        {"uid": user_id},
    ).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="User not found")
    keys = [
        "username",
        "display_name",
        "profile_picture_url",
        "email",
        "region",
        "kingdom_name",
        "alliance_name",
        "motto",
        "bio",
        "theme_preference",
        "profile_banner",
        "vip_level",
        "founder",
        "expires_at",
    ]
    profile = {k: row[i] for i, k in enumerate(keys)}
    session_rows = db.execute(
        text(
            "SELECT session_id, device, last_seen FROM user_active_sessions WHERE user_id = :uid AND session_status = 'active'"
        ),
        {"uid": user_id},
    ).fetchall()
    sessions = [
        {"session_id": r[0], "device": r[1], "last_seen": r[2]} for r in session_rows
    ]
    profile["sessions"] = sessions
    return profile


@router.post("/update")
def update_profile(
    payload: UpdatePayload,
    user_id: str = Depends(verify_jwt_token),
    db: Session = Depends(get_db),
):
    # fetch current values
    current = db.execute(
        text(
            "SELECT display_name, profile_picture_url FROM users WHERE user_id = :uid"
        ),
        {"uid": user_id},
    ).fetchone()
    customization = db.execute(
        text(
            "SELECT motto, bio, theme_preference, profile_banner FROM user_customization WHERE user_id = :uid"
        ),
        {"uid": user_id},
    ).fetchone()

    db.execute(
        text(
            "UPDATE users SET display_name = :dn, profile_picture_url = :pic WHERE user_id = :uid"
        ),
        {
            "dn": payload.display_name,
            "pic": payload.profile_picture_url,
            "uid": user_id,
        },
    )
    db.execute(
        text(
            """
            INSERT INTO user_customization (user_id, motto, bio, theme_preference, profile_banner)
            VALUES (:uid, :motto, :bio, :theme, :banner)
            ON CONFLICT (user_id)
            DO UPDATE SET motto = EXCLUDED.motto,
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

    diffs = {}
    if current:
        if payload.display_name != current[0]:
            diffs["display_name"] = payload.display_name
        if payload.profile_picture_url != current[1]:
            diffs["profile_picture_url"] = payload.profile_picture_url
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


@router.post("/logout-session")
def logout_session(
    payload: SessionPayload,
    user_id: str = Depends(verify_jwt_token),
    db: Session = Depends(get_db),
):
    row = db.execute(
        text(
            "SELECT session_id FROM user_active_sessions WHERE session_id = :sid AND user_id = :uid"
        ),
        {"sid": payload.session_id, "uid": user_id},
    ).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Session not found")
    db.execute(
        text(
            "UPDATE user_active_sessions SET session_status = 'revoked' WHERE session_id = :sid"
        ),
        {"sid": payload.session_id},
    )
    db.commit()
    log_action(db, user_id, "logout_session", payload.session_id)
    return {"message": "session revoked"}
