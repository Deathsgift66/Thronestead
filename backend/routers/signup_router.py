from fastapi import APIRouter, HTTPException, Request, Depends
from pydantic import BaseModel, EmailStr, validator
from sqlalchemy.orm import Session
from sqlalchemy import text

from services.moderation import validate_clean_text

from backend.database import get_db
from backend.models import User
from backend.supabase_client import get_supabase_client
from .signup import verify_hcaptcha

router = APIRouter(prefix="/api/signup", tags=["signup_simple"])


class SignupPayload(BaseModel):
    email: EmailStr
    password: str
    kingdom_name: str
    region: str
    profile_bio: str | None = None


class SignupCheckPayload(BaseModel):
    email: EmailStr
    kingdom_name: str
    region: str
    captcha_token: str | None = None

    @validator("kingdom_name")
    def _validate_name(cls, value: str) -> str:
        if len(value) < 3 or len(value) > 32:
            raise ValueError("Kingdom name must be between 3 and 32 characters")
        validate_clean_text(value)
        return value


@router.post("/validate")
async def validate_signup(
    payload: SignupCheckPayload,
    request: Request,
    db: Session = Depends(get_db),
):
    """Validate signup inputs before account creation."""
    sb = get_supabase_client()

    if not verify_hcaptcha(
        payload.captcha_token, request.client.host if request.client else None
    ):
        raise HTTPException(status_code=403, detail="Captcha validation failed")

    try:
        session = sb.auth.get_session()
    except Exception:  # pragma: no cover - network failure
        session = None

    user = getattr(session, "user", None) if session else None
    auth_id = getattr(user, "id", None) if user else None
    if not auth_id:
        raise HTTPException(status_code=401, detail="Authentication session not found")

    email_row = db.execute(
        text("SELECT 1 FROM users WHERE lower(email) = :e"),
        {"e": payload.email.lower()},
    ).fetchone()
    if email_row:
        raise HTTPException(status_code=409, detail="Email already in use")

    kingdom_row = db.execute(
        text("SELECT 1 FROM users WHERE kingdom_name ILIKE :k"),
        {"k": payload.kingdom_name},
    ).fetchone()
    if kingdom_row:
        raise HTTPException(status_code=409, detail="Kingdom name already taken")

    region_row = db.execute(
        text(
            "SELECT region_name FROM region_catalogue "
            "WHERE region_code = :r OR region_name ILIKE :rn"
        ),
        {"r": payload.region, "rn": payload.region},
    ).fetchone()
    if not region_row:
        raise HTTPException(status_code=400, detail="Selected region is invalid")
    region_name = region_row[0]

    return {
        "status": "ok",
        "message": "All signup inputs are available and valid.",
        "auth_user_id": auth_id,
    }


@router.post("/create")
async def create_user(
    payload: SignupPayload, request: Request, db: Session = Depends(get_db)
):
    sb = get_supabase_client()
    client_ip = request.client.host if request.client else None

    if len(payload.kingdom_name) < 3 or len(payload.kingdom_name) > 32:
        raise HTTPException(status_code=400, detail="Invalid kingdom name")
    try:
        validate_clean_text(payload.kingdom_name)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    row = db.execute(
        text(
            "SELECT region_name FROM region_catalogue "
            "WHERE region_code = :r OR region_name = :rn"
        ),
        {"r": payload.region, "rn": payload.region},
    ).fetchone()
    if not row:
        raise HTTPException(status_code=400, detail="Invalid region")
    region_name = row[0]

    try:
        auth_resp = sb.auth.admin.create_user(
            {
                "email": payload.email,
                "password": payload.password,
                "email_confirm": True,
            }
        )
        auth_user = getattr(auth_resp, "user", None) or getattr(
            auth_resp, "data", {}
        ).get("user")
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
            region=region_name,
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
