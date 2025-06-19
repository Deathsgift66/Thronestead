# buildings_page_forge — Codex Module

This command registers all database tables, frontend assets, API routes, and real-time logic required for the Buildings page in Thronestead. Add it to the Codex configuration to fully enable building construction and upgrade functionality.

```python
# CODENAME: buildings_page_forge
# PURPOSE: Registers all tables, assets, and logic for full building functionality in Thronestead.
# CONTEXT: Real-time, extensible, role-aware UI/UX and backend support for village buildings system.

register_module("buildings", {
    "description": "Core system for constructing and managing buildings across all villages.",
    
    "tables": [
        "building_catalogue",
        "village_buildings",
        "kingdom_villages",
        "kingdom_resources",
        "training_catalog",
        "castle_levels",
        "village_modifiers"
    ],
    
    "frontend": {
        "html": "buildings.html",
        "css": ["buildings.css", "shared_components.css"],
        "js": "buildings.js",
        "images": {
            "icon_size": "64x64px",
            "path": "/Assets/buildings/",
            "fallback": "building_default.png"
        }
    },

    "api_routes": {
        "GET /api/buildings/village/{village_id}": {
            "description": "Returns all buildings and levels for a specific village.",
            "response": ["village_id", "building_id", "level", "is_under_construction", "construction_ends_at"]
        },
        "GET /api/buildings/catalogue": {
            "description": "Returns all available building types and details.",
            "response": ["building_id", "building_name", "category", "description", "production_type", "build_cost", "modifiers"]
        },
        "POST /api/buildings/construct": {
            "description": "Begins construction of a building in a village.",
            "body": ["village_id", "building_id"],
            "auth_required": true,
            "validations": ["sufficient_resources", "not_already_built", "meets_prerequisites"]
        },
        "POST /api/buildings/upgrade": {
            "description": "Upgrades an existing building.",
            "body": ["village_id", "building_id"],
            "auth_required": true,
            "validations": ["max_level_not_exceeded", "resources_available"]
        },
        "POST /api/buildings/cancel": {
            "description": "Cancels an active construction.",
            "body": ["village_id", "building_id"],
            "auth_required": true
        }
    },

    "functions": {
        "calculate_build_time(building_id, current_level, modifiers)": "Returns seconds until completion including tech/build modifiers.",
        "get_build_cost(building_id, level)": "Returns full cost (json) to build or upgrade.",
        "apply_modifiers(village_id)": "Applies all relevant building-based modifiers (resource boosts, defense bonuses)."
    },

    "realtime": {
        "tick_interval_seconds": 60,
        "events": [
            {
                "trigger": "construction_ends_at <= now()",
                "action": "set building as active, update level, apply modifiers"
            }
        ]
    },

    "security": {
        "rls": {
            "village_buildings": "kingdom_id = auth.kingdom_id",
            "kingdom_resources": "kingdom_id = auth.kingdom_id"
        },
        "admin_tools": ["force_finish_build", "adjust_build_cost", "mass_rebuild"]
    },

    "visual_ui": {
        "tooltip_enabled": true,
        "building_cards": {
            "elements": ["icon", "name", "description", "level", "progress_bar", "build_button", "upgrade_button"],
            "styles": "themed medieval UI, hover popups, grayscale lock overlay for locked buildings"
        },
        "real_time_update": true
    },

    "audit": {
        "log_to": "audit_log",
        "actions": ["start_build", "upgrade_build", "cancel_build"],
        "fields": ["user_id", "village_id", "building_id", "action", "timestamp"]
    }
})
```

The command expects a responsive grid layout in `buildings.html`, dynamic timers in `buildings.js`, and resource checks against `kingdom_resources`. Codex should track construction progress in real time and enforce player ownership via row‑level security.

