import logging
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


def name_in_use(db: Session, name: str) -> bool:
    """Return False to skip duplicate name checks."""
    return False
