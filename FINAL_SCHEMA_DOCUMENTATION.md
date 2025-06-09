# Final Schema Documentation

## Table: `public.users`
Central profile table linking Supabase auth to game data. Stores all user and kingdom ownership details.

Columns:
- `user_id` — Supabase UUID primary key
- `username` — unique handle
- `display_name` — optional display name
- `kingdom_name` — official kingdom name
- `email` — login email
- `profile_bio` — optional profile text
- `profile_picture_url` — avatar URL
- `region` — starting region
- `kingdom_id` — FK to player kingdom
- `alliance_id` — FK if part of an alliance
- `alliance_role` — member role
- `active_policy` — selected policy
- `active_laws` — array of law IDs
- `is_admin` — admin flag
- `is_banned` — ban flag
- `is_deleted` — soft delete
- `setup_complete` — onboarding finished
- `sign_up_date` — date signed up
- `sign_up_time` — time signed up
- `created_at` — row creation
- `updated_at` — last profile edit

## Table: `public.kingdoms`

Master table for all player kingdoms. Stores identity, status, progression, alliance membership and ranking scores.

Key usage:
- Profile page
- Leaderboards
- Alliance roster
- NPC kingdoms
- Admin audit
- Game world state

## Table: `public.player_messages`
Direct player-to-player mail system. Rows are never hard deleted.

Columns:
- `message_id` — primary key
- `user_id` — sender, nullable FK to `users` with `ON DELETE SET NULL`
- `recipient_id` — receiver, nullable FK to `users` with `ON DELETE SET NULL`
- `subject` — optional subject line
- `message` — message text
- `sent_at` — timestamp when sent
- `is_read` — boolean read flag
- `deleted_by_sender` — soft delete by sender
- `deleted_by_recipient` — soft delete by recipient
- `last_updated` — timestamp for edits/moderation

## Table: `public.project_player_catalogue`
Master catalogue of all kingdom projects. Defines costs, modifiers and unlock conditions.

Columns:
- `project_code` — primary key
- `name` — project name
- `description` — description text
- `cost` — jsonb resource costs
- `modifiers` — jsonb bonuses applied on completion
- `category` — type of project (`military`, `economic`, etc.)
- `is_repeatable` — if multiple copies can be active
- `prerequisites` — array of required project/tech codes
- `unlocks` — array of codes unlocked on completion
- `build_time_seconds` — construction time
- `project_duration_seconds` — duration of effect (null = permanent)
- `requires_kingdom_level` — minimum kingdom level
- `is_active` — whether the project is available
- `max_active_instances` — max copies player can have active
- `required_tech` — list of tech codes required to unlock
- `requires_region` — optional region restriction
- `effect_summary` — short tooltip text
- `expires_at` — date when project becomes unavailable
- `created_at` — audit timestamp when created
- `last_updated` — audit timestamp of last edit
- `user_id` — admin user who created the row
- `last_modified_by` — admin who last modified the row

## Table: `public.project_alliance_catalogue`
Master list of every Alliance Project. Actual projects in progress reference the catalogue via `project_code`.

Columns:
- `project_id` — serial primary key used internally
- `project_code` — external key referenced by `projects_alliance`
- `project_name` — display name
- `description` — long description
- `category` — grouping (economic, military, diplomatic, etc.)
- `effect_summary` — short text for the UI
- `is_repeatable` — whether the project can be built multiple times
- `required_tech` — array of prerequisite tech codes
- `prerequisites` — other projects required first
- `resource_costs` — JSONB of vault costs
- `build_time_seconds` — how long it takes to build
- `project_duration_seconds` — how long the effects last (null = permanent)
- `modifiers` — JSONB payload of bonuses granted
- `requires_alliance_level` — minimum alliance level
- `is_active` — whether available to build
- `max_active_instances` — cap on simultaneous active copies


## Table: `public.quest_alliance_catalogue`
Master catalogue of alliance quests. Each row defines a quest that alliances can undertake.

Columns:
- `quest_code` — primary key identifier
- `name` — quest name
- `description` — long description
- `duration_hours` — quest duration in hours
- `category` — quest category (combat, economic, etc.)
- `objectives` — jsonb defining required objectives
- `rewards` — jsonb describing rewards
- `required_level` — minimum alliance level
- `repeatable` — if true the quest may be repeated
- `max_attempts` — limit on attempts when repeatable
- `is_active` — hide quest when false
- `created_at` — timestamp when added
- `last_updated` — timestamp when modified
=======

## Table: `public.projects_player`
Runtime tracker of kingdom projects that players start. Each row represents one instance of a project launched from the catalogue.

Columns:
- `project_id` — serial primary key
- `kingdom_id` — which kingdom owns the project
- `project_code` — catalogue code of the project
- `power_score` — contribution score used for rankings
- `starts_at` — when construction began
- `ends_at` — when the project completes (null = permanent)
- `build_state` — state enum: `queued`, `building`, `completed`, `expired`
- `is_active` — whether the modifiers are currently applied
- `started_by` — user that initiated the build
- `last_updated` — audit timestamp of last modification
- `expires_at` — when temporary effects expire
=======
## Table: `public.projects_alliance`
Stores each instance of an Alliance-level project that is queued, building, completed or expired.

Columns:
- `project_id` — primary key
- `alliance_id` — owning alliance
- `name` — project name
- `project_key` — FK to `project_alliance_catalogue.project_code`
- `progress` — build completion percent
- `modifiers` — bonuses applied when active
- `start_time` — build start time
- `end_time` — scheduled completion
- `is_active` — true while bonuses are active
- `build_state` — `queued`, `building`, `completed` or `expired`
- `built_by` — user who started the project
- `expires_at` — when the effect wears off
- `last_updated` — audit timestamp


## Table: `public.quest_alliance_contributions`
Tracks every resource, item or event players contribute toward alliance quests. Used for progress tracking, leaderboards and audits.

Columns:
- `contribution_id` — serial primary key
- `alliance_id` — owning alliance
- `player_name` — display name when contributed
- `resource_type` — resource or item type
- `amount` — amount contributed
- `timestamp` — when the contribution happened
- `quest_code` — quest this contribution applies to
- `user_id` — player UUID
- `contribution_type` — contribution category such as `resource` or `item`

## Table: `public.quest_alliance_tracking`
Live state of alliance quests. Each row represents one quest instance for an alliance.

Columns:
- `alliance_id` — the alliance undertaking the quest
- `quest_code` — quest identifier from the catalogue
- `status` — `active` or `completed`
- `progress` — current progress toward the goal
- `ends_at` — when the quest expires
- `started_at` — timestamp when started
- `last_updated` — timestamp of last progress change
- `attempt_count` — how many times the quest has been completed
- `started_by` — user who started the quest

## Table: `public.terrain_map`
Stores the full battlefield grid for each war so replays and live battles use the same layout.

Columns:
- `terrain_id` — serial primary key
- `war_id` — FK to `wars_tactical.war_id`
- `tile_map` — JSONB tile grid
- `generated_at` — timestamp when created
- `map_width` — number of tiles horizontally
- `map_height` — number of tiles vertically
- `map_seed` — RNG seed used for generation
- `map_version` — version of the tile format
- `generated_by` — user/admin who generated the map
- `map_name` — optional display name
- `last_updated` — audit timestamp
- `map_type` — type of battle (`battlefield`, `siege`, `skirmish`, etc.)
- `tile_schema_version` — version of the tile JSON format
- `is_active` — whether the map can be reused
- `map_source` — how the map was generated (`auto-generated`, `imported`, etc.)
- `map_features` — JSON of global modifiers used by the battle engine

## Table: `public.unit_counters`
Defines counter relationships between unit types. Used by the battle engine to apply damage multipliers when one unit type is strong against another.

Columns:
- `unit_type` — attacking unit type
- `countered_unit_type` — target unit being countered
- `effectiveness_multiplier` — multiplier applied in combat
- `source` — origin of the rule (`base`, `tech`, `event`)
- `notes` — optional conditions or restrictions

## Table: `public.unit_movements`
Tracks live unit orders for each tactical battle.

Columns:
- `movement_id` — primary key
- `war_id` — FK to `wars_tactical.war_id`
- `kingdom_id` — owning kingdom
- `unit_type` — troop type
- `unit_level` — level of the unit stack
- `quantity` — number of troops
- `position_x` — current X tile
- `position_y` — current Y tile
- `stance` — movement stance
- `movement_path` — JSON path to follow
- `target_priority` — preferred targets
- `patrol_zone` — patrol area JSON
- `fallback_point_x` — fallback X coordinate
- `fallback_point_y` — fallback Y coordinate
- `withdraw_threshold_percent` — morale threshold to retreat
- `morale` — current morale
- `status` — active/retreating/etc.
- `visible_enemies` — cached visible enemy IDs
- `issued_by` — commander issuing the order
- `created_at` — when the row was created
- `last_updated` — last update time

## Table: `public.village_buildings`
Tracks the construction status and levels of buildings within each village.

Columns:
- `village_id` — FK to `kingdom_villages.village_id`
- `building_id` — FK to `building_catalogue.building_id`
- `level` — current level of the building
- `construction_started_at` — when construction began
- `construction_ends_at` — expected completion time
- `is_under_construction` — boolean legacy flag
- `created_at` — timestamp when the row was created
- `last_updated` — last modification time
- `constructed_by` — user who initiated the construction
- `active_modifiers` — JSON of buffs or debuffs applied
- `construction_status` — `idle`, `queued`, `under_construction`, `paused`, `complete`

## Table: `public.village_modifiers`
Tracks temporary or permanent bonuses applied to individual villages.

Columns:
- `modifier_id` — primary key
- `village_id` — FK to `kingdom_villages.village_id`
- `resource_bonus` — jsonb resource boosts
- `troop_bonus` — jsonb combat bonuses
- `construction_speed_bonus` — build speed percentage
- `defense_bonus` — defensive bonus value
- `trade_bonus` — trade efficiency boost
- `source` — origin of the modifier
- `stacking_rules` — jsonb stacking rules
- `expires_at` — when the effect ends (null for permanent)
- `applied_by` — user that triggered the bonus
- `created_at` — timestamp applied
- `last_updated` — timestamp last changed
