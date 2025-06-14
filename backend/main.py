# Project Name: Kingmakers Rise©
# File Name: main.py
# Version: 6.13.2025.19.49
# Developer: Deathsgift66

"""
Main application entry point for the FastAPI server powering Kingmakers Rise©.
Loads routers, initializes the DB schema, and serves static frontend content.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import logging
import os

logger = logging.getLogger("KingmakersRise.BackendMain")

from .database import engine
from .models import Base
from .data import load_game_settings
from .routers import (
    admin,
    admin_dashboard,
    alliance_members,
    alliance_members_view,
    alliance_management,
    alliance_projects,
    kingdom,
    conflicts,
    black_market,
    black_market_routes,
    news,
    alliance_wars,
    notifications,
    battle,
    alliance_quests,
    alliance_changelog,
    changelog,
    kingdom_military,
    alliance_vault,
    audit_log,
    admin_audit_log,
    donate_vip,
    forgot_password,
    messages,
    compose,
    player_management,
    market,
    diplomacy,
    diplomacy_center,
    leaderboard,
    homepage,
    buildings,
    tutorial,
    region,
    progression_router,
    villages_router,
    vip_status_router,
    titles_router,
    treaties_router,
    alliance_treaties_router,
    account_settings,
    spies_router,
    policies_laws as policies_laws_router,
    overview as overview_router,
    legal,
    trade_logs,
    training_history,
    training_catalog,
    training_queue,
    village_modifiers,
    settings_router,
    alliance_home,
    wars,
    quests_router,
    projects_router,
    resources,
    kingdom_history,
    kingdom_achievements,
    login_routes,
    profile_view,
    navbar,
    seasonal_effects,
    signup as signup_router,
    treaty_web,
    village_master as village_master_router,
    vacation_mode,
    world_map,
    health,
    public_config,
)

# -----------------------
# ⚙️ FastAPI Initialization
# -----------------------
app = FastAPI(
    title="Kingmaker's Rise API",
    version="6.13.2025.19.49",
    description="Backend for the Kingmakers Rise strategy MMO.",
)

# -----------------------
# 🔐 Middleware (CORS, security headers, etc.)
# -----------------------
allowed_origins_env = os.getenv("ALLOWED_ORIGINS")
if allowed_origins_env:
    origins = [o.strip() for o in allowed_origins_env.split(",") if o.strip()]
else:
    origins = []  # Secure default when env var is missing
    logger.warning(
        "ALLOWED_ORIGINS not set; CORS disabled for external domains."
    )

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -----------------------
# 🗃️ Ensure Database Tables Exist
# -----------------------
if engine:
    Base.metadata.create_all(bind=engine)

# Load game-wide settings into memory (affects all systems)
load_game_settings()

# -----------------------
# 📦 Route Imports and Inclusion
# -----------------------

routers = [
    admin, admin_dashboard, alliance_members, alliance_members_view, alliance_management, alliance_projects,
    kingdom, conflicts, black_market, black_market_routes, news, tutorial, homepage,
    region, alliance_wars, notifications, battle, alliance_quests, alliance_changelog,
    changelog, kingdom_military, alliance_vault, audit_log, admin_audit_log, donate_vip,
    messages, compose, player_management, market, diplomacy, diplomacy_center,
    leaderboard, buildings, progression_router, villages_router, vip_status_router,
    titles_router, treaties_router, alliance_treaties_router, account_settings, spies_router,
    policies_laws_router, trade_logs, training_history, training_catalog, training_queue,
    village_modifiers, settings_router, alliance_home, wars, quests_router, projects_router,
    resources, kingdom_history, kingdom_achievements, forgot_password, login_routes,
    legal, profile_view, navbar, seasonal_effects, signup_router, treaty_web,
    village_master_router, vacation_mode, world_map, health, overview_router, public_config
]

# Register all API routers
for router in routers:
    app.include_router(router.router)

# Include optional alt router for alliance vault (used for separate auth context or internal ops)
app.include_router(alliance_vault.alt_router)

# -----------------------
# 🖼️ Serve Static Frontend Files
# -----------------------
BASE_DIR = Path(__file__).resolve().parent.parent
app.mount("/", StaticFiles(directory=BASE_DIR, html=True), name="static")

# -----------------------
# ✅ Health Check (used by Render or CI/CD)
# -----------------------
@app.get("/health-check")
def health_check():
    return {"status": "online", "service": "Kingmaker's Rise API"}
