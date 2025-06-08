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
