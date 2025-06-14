# Project Name: Kingmakers Rise©
# File Name: signup.py
# Version 6.13.2025.19.49
# Developer: Deathsgift66

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, EmailStr, constr
from typing import Optional
from sqlalchemy import text
from sqlalchemy.orm import Session

from backend.models import Notification

from ..supabase_client import get_supabase_client
from ..database import get_db

router = APIRouter(prefix="/api/signup", tags=["signup"])


# ------------- Payload Models -------------------

class CheckPayload(BaseModel):
    kingdom_name: Optional[str] = None
    username: Optional[constr(min_length=3, max_length=20)] = None


class CreateUserPayload(BaseModel):
    user_id: str
    username: str
    display_name: str
    kingdom_name: str
    email: EmailStr


class RegisterPayload(BaseModel):
    email: EmailStr
    password: constr(min_length=6)
    username: constr(min_length=3, max_length=20)
    kingdom_name: str
    display_name: str


# ------------- Route Endpoints -------------------

@router.post("/check")
def check_availability(payload: CheckPayload):
    """
    Check if a kingdom name or username is available.
    """
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

    except Exception as exc:
        raise HTTPException(status_code=500, detail="Failed to query availability") from exc

    return {
        "kingdom_available": available_kingdom,
        "username_available": available_username
    }


@router.get("/stats")
def signup_stats():
    """
    Return top kingdoms for display on the signup screen.
    """
    sb = get_supabase_client()
    try:
        res = (
            sb.table("leaderboard_kingdoms")
            .select("kingdom_name,score")
            .order("score", desc=True)
            .limit(3)
            .execute()
        )
        data = getattr(res, "data", res) or []
        return {"top_kingdoms": data}
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Failed to fetch kingdom stats") from exc


@router.post("/create_user")
def create_user(payload: CreateUserPayload, db: Session = Depends(get_db)):
    """
    Create the user's basic profile record after authentication setup.
    """
    try:
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

        db.execute(
            text(
                """
                INSERT INTO user_setting_entries (user_id, setting_key, setting_value)
                VALUES (:uid, 'theme', 'default')
                ON CONFLICT DO NOTHING
                """
            ),
            {"uid": payload.user_id},
        )

        db.add(
            Notification(
                user_id=payload.user_id,
                title="Welcome to Kingmaker’s Rise!",
                message="Your kingdom awaits.",
                category="system",
            )
        )

        db.commit()
        return {"status": "created"}
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to create user") from e


@router.post("/register")
def register(payload: RegisterPayload, db: Session = Depends(get_db)):
    """
    Create a Supabase auth user and register their kingdom profile.
    """
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
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Failed to create auth user") from exc

    # Extract the newly created user ID
    uid = (
        getattr(res, "user", None) and getattr(res.user, "id", None)
    ) or getattr(res, "id", None)

    if not uid:
        raise HTTPException(status_code=500, detail="Signup failed - user ID missing")

    try:
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

        db.execute(
            text(
                """
                INSERT INTO user_setting_entries (user_id, setting_key, setting_value)
                VALUES (:uid, 'theme', 'default')
                ON CONFLICT DO NOTHING
                """
            ),
            {"uid": uid},
        )

        db.add(
            Notification(
                user_id=uid,
                title="Welcome to Kingmaker’s Rise!",
                message="Your kingdom awaits.",
                category="system",
            )
        )

        db.commit()
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Failed to save user profile") from exc

    return {"user_id": uid}
