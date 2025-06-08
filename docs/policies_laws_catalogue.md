# Policies & Laws Catalogue

This table defines every policy or law that can exist in the game. The catalogue is referenced when presenting choices to players and during game logic when applying active modifiers.

## Table: `public.policies_laws_catalogue`

| Column | Purpose |
| --- | --- |
| `id` | Primary key. Unique policy or law ID. |
| `type` | `policy` or `law`. |
| `name` | Display name. |
| `description` | Full description of the rule. |
| `effect_summary` | Short text summary for the UI. |
| `category` | Grouping such as Economy, Military, Diplomacy, Religion. |
| `modifiers` | JSON modifiers applied to game calculations. |
| `unlock_at_level` | Minimum castle level required. |
| `is_active` | Admin toggle to disable a rule. |
| `created_at` | When the row was created. |
| `last_updated` | Last time this row changed. |

## Usage

Load available options for the Policies & Laws screen:
```sql
SELECT * FROM public.policies_laws_catalogue
WHERE is_active = true
ORDER BY unlock_at_level, id;
```

A player's selections are stored on the `users` table using `active_policy` and `active_laws[]`. When calculating effects, join to this catalogue and use the `modifiers` JSON to apply bonuses or penalties.

Only administrators should modify this catalogue so that gameplay rules remain consistent.
