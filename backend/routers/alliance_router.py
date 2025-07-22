from fastapi import APIRouter

# Consolidated alliance router that aggregates all alliance-related routers.

from . import (
    alliance_achievements,
    alliance_bank,
    alliance_changelog,
    alliance_home,
    alliance_loans,
    alliance_management,
    alliance_members,
    alliance_members_api,
    alliance_members_view,
    alliance_policies,
    alliance_projects,
    alliance_quests,
    alliance_roles,
    alliance_treaties_router,
    alliance_vault,
    alliance_votes,
    alliance_wars,
)

router = APIRouter()

for mod in [
    alliance_achievements,
    alliance_bank,
    alliance_changelog,
    alliance_home,
    alliance_loans,
    alliance_management,
    alliance_members,
    alliance_members_api,
    alliance_members_view,
    alliance_policies,
    alliance_projects,
    alliance_quests,
    alliance_roles,
    alliance_treaties_router,
    alliance_vault,
    alliance_votes,
    alliance_wars,
]:
    router.include_router(mod.router)

