# Final Schema Documentation

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

