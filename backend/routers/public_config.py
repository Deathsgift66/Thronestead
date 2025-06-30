from ..env_utils import get_env_var
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..database import get_db
from services.system_flag_service import get_flag

router = APIRouter(prefix="/api/public-config", tags=["config"])


@router.get("/")
def public_config(db: Session = Depends(get_db)):
    """Expose public Supabase configuration for the frontend."""
    maintenance_default = (
        get_env_var("MAINTENANCE_MODE", default="false").lower() == "true"
    )
    return {
        "SUPABASE_URL": get_env_var("SUPABASE_URL"),
        "SUPABASE_ANON_KEY": get_env_var("SUPABASE_ANON_KEY"),
        "MAINTENANCE_MODE": get_flag(db, "maintenance_mode", maintenance_default),
        "FALLBACK_OVERRIDE": get_flag(db, "fallback_override", False),
    }
