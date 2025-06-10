from fastapi import FastAPI
from .routers import (
    admin,
    alliance_members,
    alliance_projects,
    kingdom,
    conflicts,
    black_market,
    news,
    alliance_wars,
    notifications,
    battle,
    alliance_quests,
    changelog,
    kingdom_military,
    alliance_vault,
    audit_log,
    donate_vip,
    messages,
    player_management,
    market,
    diplomacy,
    leaderboard,
    buildings,
    progression_router,
    villages_router,
    vip_status_router,
    titles_router,
    treaties_router,
    alliance_treaties_router,
    admin_dashboard,
    account_settings,
    spies_router,
    trade_logs,
    training_history,
    village_modifiers,
    settings_router,
    alliance_home,
    wars,
    quests_router,
    projects_router,
    kingdom_history,
)
from .database import engine
from .models import Base
from .data import load_game_settings

app = FastAPI(title="Kingmaker's Rise API")

# Ensure tables exist
Base.metadata.create_all(bind=engine)
load_game_settings()

app.include_router(alliance_members.router)
app.include_router(admin.router)
app.include_router(admin_dashboard.router)
app.include_router(alliance_projects.router)
app.include_router(kingdom.router)
app.include_router(conflicts.router)
app.include_router(black_market.router)
app.include_router(news.router)
app.include_router(alliance_wars.router)
app.include_router(notifications.router)
app.include_router(battle.router)
app.include_router(alliance_quests.router)
app.include_router(changelog.router)
app.include_router(kingdom_military.router)
app.include_router(alliance_vault.router)
app.include_router(audit_log.router)
app.include_router(donate_vip.router)
app.include_router(messages.router)
app.include_router(player_management.router)
app.include_router(market.router)
app.include_router(diplomacy.router)
app.include_router(leaderboard.router)
app.include_router(buildings.router)
app.include_router(progression_router.router)
    app.include_router(villages_router.router)
    app.include_router(vip_status_router.router)
    app.include_router(titles_router.router)
    app.include_router(treaties_router.router)
    app.include_router(alliance_treaties_router.router)
    app.include_router(account_settings.router)
    app.include_router(spies_router.router)
app.include_router(trade_logs.router)
app.include_router(training_history.router)
app.include_router(village_modifiers.router)
app.include_router(settings_router.router)
app.include_router(alliance_home.router)
app.include_router(wars.router)
app.include_router(quests_router.router)
app.include_router(projects_router.router)
app.include_router(kingdom_history.router)

