from fastapi import APIRouter, HTTPException, Request, Depends
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session
from sqlalchemy import text

from services.moderation import validate_clean_text

from backend.database import get_db
from backend.models import User
from backend.supabase_client import get_supabase_client

router = APIRouter(prefix="/api/signup", tags=["signup_simple"])


class SignupPayload(BaseModel):
    email: EmailStr
    password: str
    kingdom_name: str
    region: str
    profile_bio: str | None = None


@router.post("/create")
async def create_user(payload: SignupPayload, request: Request, db: Session = Depends(get_db)):
    sb = get_supabase_client()
    client_ip = request.client.host if request.client else None

    if len(payload.kingdom_name) < 3 or len(payload.kingdom_name) > 32:
        raise HTTPException(status_code=400, detail="Invalid kingdom name")
    try:
        validate_clean_text(payload.kingdom_name)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    row = db.execute(
        text("SELECT 1 FROM region_catalogue WHERE region_name = :r"),
        {"r": payload.region},
    ).fetchone()
    if not row:
        raise HTTPException(status_code=400, detail="Invalid region")

    try:
        auth_resp = sb.auth.admin.create_user({
            "email": payload.email,
            "password": payload.password,
            "email_confirm": True,
        })
        auth_user = getattr(auth_resp, "user", None) or getattr(auth_resp, "data", {}).get("user")
        auth_user_id = getattr(auth_user, "id", None) or (auth_user or {}).get("id")
        if not auth_user_id:
            raise ValueError("Missing auth user id")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Auth creation failed: {e}")

    try:
        new_user = User(
            user_id=auth_user_id,
            email=payload.email,
            kingdom_name=payload.kingdom_name,
            region=payload.region,
            profile_bio=payload.profile_bio,
            auth_user_id=auth_user_id,
            sign_up_ip=client_ip,
            username=payload.kingdom_name,
        )
        db.add(new_user)
        db.commit()
    except Exception as e:
        sb.auth.admin.delete_user(auth_user_id)
        db.rollback()
        raise HTTPException(status_code=500, detail=f"DB user creation failed: {e}")

    return {"message": "Signup complete"}
