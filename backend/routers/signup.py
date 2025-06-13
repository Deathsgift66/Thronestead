
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
from sqlalchemy import text
from sqlalchemy.orm import Session

from ..supabase_client import get_supabase_client
from ..database import get_db


router = APIRouter(prefix="/api/signup", tags=["signup"])


class CheckPayload(BaseModel):
    kingdom_name: Optional[str] = None
    username: Optional[str] = None


@router.post("/check")
def check_availability(payload: CheckPayload):
    """Check if kingdom or username is available."""
    sb = get_supabase_client()
    available_kingdom = True
    available_username = True
    try:
        if payload.kingdom_name:
            res = (
                sb.table("kingdoms")
                .select("kingdom_id")
                .eq("kingdom_name", payload.kingdom_name)
                .limit(1)
                .execute()
            )
            rows = getattr(res, "data", res) or []
            available_kingdom = len(rows) == 0
        if payload.username:
            res = (
                sb.table("users")
                .select("id")
                .eq("username", payload.username)
                .limit(1)
                .execute()
            )
            rows = getattr(res, "data", res) or []
            available_username = len(rows) == 0
    except Exception as exc:  # pragma: no cover - network/db errors
        raise HTTPException(status_code=500, detail="failed to query") from exc

    return {"kingdom_available": available_kingdom, "username_available": available_username}


@router.get("/stats")
def signup_stats():
    """Return top kingdom stats for signup page."""
    sb = get_supabase_client()
    try:
        res = (
            sb.table("leaderboard_kingdoms")
            .select("kingdom_name,score")
            .order("score", desc=True)
            .limit(3)
            .execute()
        )
    except Exception as exc:  # pragma: no cover - network/db errors
        raise HTTPException(status_code=500, detail="failed to fetch stats") from exc

    data = getattr(res, "data", res) or []
    return {"top_kingdoms": data}


class CreateUserPayload(BaseModel):
    user_id: str
    username: str
    display_name: str
    kingdom_name: str
    email: str


@router.post("/create_user")
def create_user(payload: CreateUserPayload, db: Session = Depends(get_db)):
    """Insert a basic profile row when a new account is registered."""
    db.execute(
        text(
            """
            INSERT INTO users (user_id, username, display_name, kingdom_name, email)
            VALUES (:uid, :username, :display, :kingdom, :email)
            ON CONFLICT (user_id) DO NOTHING
            """
        ),
        {
            "uid": payload.user_id,
            "username": payload.username,
            "display": payload.display_name,
            "kingdom": payload.kingdom_name,
            "email": payload.email,
        },
    )
    db.commit()
    return {"status": "created"}


class RegisterPayload(BaseModel):
    email: str
    password: str
    username: str
    kingdom_name: str
    display_name: str


@router.post("/register")
def register(payload: RegisterPayload, db: Session = Depends(get_db)):
    """Create auth user and corresponding profile."""
    sb = get_supabase_client()
    try:
        res = sb.auth.admin.create_user(
            email=payload.email,
            password=payload.password,
            user_metadata={
                "display_name": payload.display_name,
                "username": payload.username,
            },
        )
    except Exception as exc:  # pragma: no cover - network/db errors
        raise HTTPException(status_code=500, detail="failed to create auth user") from exc

    uid = (
        getattr(res, "user", None) and getattr(res.user, "id", None)
    ) or getattr(res, "id", None)
    if not uid:
        raise HTTPException(status_code=500, detail="signup failed")

    db.execute(
        text(
            """
            INSERT INTO users (user_id, username, display_name, kingdom_name, email, auth_user_id)
            VALUES (:uid, :username, :display, :kingdom, :email, :uid)
            ON CONFLICT (user_id) DO NOTHING
            """
        ),
        {
            "uid": uid,
            "username": payload.username,
            "display": payload.display_name,
            "kingdom": payload.kingdom_name,
            "email": payload.email,
        },
    )
    db.commit()
    return {"user_id": uid}
