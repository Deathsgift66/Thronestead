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

## Usage

Load available options for the Policies & Laws screen:
```sql
SELECT * FROM public.policies_laws_catalogue
ORDER BY id;
```

A player's selections are stored on the `users` table using `active_policy` and `active_laws[]`. Use `effect_summary` to describe the impact in the UI and apply game logic accordingly.

Only administrators should modify this catalogue so that gameplay rules remain consistent.
