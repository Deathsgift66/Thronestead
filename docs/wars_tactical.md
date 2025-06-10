# public.wars_tactical — Codex Integration Guide

This table governs all real‑time tactical wars. It tracks the current phase,
battle progress and various configuration flags used by the battle engine.

## Table Structure

| Column | Purpose / Usage |
| --- | --- |
| `war_id` | Primary key, links to `public.wars` |
| `attacker_kingdom_id` | Attacking kingdom |
| `defender_kingdom_id` | Defending kingdom |
| `phase` | `'alert'`, `'planning'`, `'live'`, `'resolved'` |
| `castle_hp` | Current HP of the defender's castle |
| `battle_tick` | Tick counter (0–12) |
| `war_status` | `active`, `paused`, `ended` |
| `terrain_id` | FK to `terrain_map` for the battlefield |
| `current_turn` | `'attacker'` or `'defender'` in turn‑based modes |
| `attacker_score` | Running score for the attacker |
| `defender_score` | Running score for the defender |
| `last_tick_processed_at` | Timestamp when the last tick executed |
| `tick_interval_seconds` | Seconds between ticks (default 300) |
| `is_concluded` | Set to true when the war is finalized |
| `started_at` | When the battle went live |
| `ended_at` | When the war ended |
| `fog_of_war` | Enable fog of war logic |
| `weather` | Optional weather modifier |
| `submitted_by` | User or admin who started the war |

## Usage Patterns
1. **War creation** – insert a row with phase `'alert'` and `war_status` `'active'`.
2. **Tick engine** – read `battle_tick`, `last_tick_processed_at` and
   `tick_interval_seconds` to pace the battle loop.
3. **Resolution** – when `castle_hp` reaches zero or other conditions are met,
   set `phase` to `'resolved'`, `war_status` to `'ended'` and `is_concluded` to
   `true`.

## Best Practices
- Update `last_tick_processed_at` after each tick.
- Use `terrain_id` to load the correct map.
- Respect `fog_of_war` and `weather` modifiers when calculating vision and
  movement.
- `castle_hp = 0` should immediately end the war in favor of the attacker.
- Phases should progress `alert → planning → live → resolved`.
