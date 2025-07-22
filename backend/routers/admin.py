"""Consolidated admin routers for Thronestead.

This module exposes a single ``router`` containing all admin related routes.
Existing admin router modules are kept under ``_admin_*.py`` and are included
here for centralized access.
"""

from fastapi import APIRouter

from . import (
    _admin_main,
    _admin_audit_log,
    _admin_dashboard,
    _admin_emergency_tools,
    _admin_events,
    _admin_news,
    _admin_system,
    _admin_ws,
)

router = APIRouter()
router.include_router(_admin_main.router)
router.include_router(_admin_audit_log.router)
router.include_router(_admin_dashboard.router)
router.include_router(_admin_emergency_tools.router)
router.include_router(_admin_events.router)
router.include_router(_admin_news.router)
router.include_router(_admin_system.router)
router.include_router(_admin_ws.router)

# Re-export public objects from the submodules for backward compatibility
from ._admin_main import *  # noqa: F401,F403
from ._admin_audit_log import *  # noqa: F401,F403
from ._admin_dashboard import *  # noqa: F401,F403
from ._admin_emergency_tools import *  # noqa: F401,F403
from ._admin_events import *  # noqa: F401,F403
from ._admin_news import *  # noqa: F401,F403
from ._admin_system import *  # noqa: F401,F403
from ._admin_ws import *  # noqa: F401,F403

__all__ = ["router"]
