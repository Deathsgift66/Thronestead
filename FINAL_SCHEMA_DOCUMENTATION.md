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
