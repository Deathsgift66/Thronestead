# public.unit_movements — Codex Integration Guide

This table tracks every unit's movement and morale during tactical battles. Each row represents the current order for a stack of troops in an ongoing war.

## Table Structure

| Column | Meaning |
| --- | --- |
| `movement_id` | Primary key for internal updates |
| `war_id` | Linked war from `wars_tactical` |
| `kingdom_id` | Which kingdom the unit belongs to |
| `unit_type` | Troop type from `unit_stats` |
| `unit_level` | Level of the unit stack |
| `quantity` | Number of troops in this order |
| `position_x` | Current X tile (0–59) |
| `position_y` | Current Y tile (0–19) |
| `stance` | `'aggressive'`, `'defensive'`, `'fallback'`, `'patrol'` |
| `movement_path` | JSON array of tiles to follow |
| `target_priority` | JSON list of preferred enemy types |
| `patrol_zone` | JSON defining patrol area |
| `fallback_point_x` | X coordinate for fallback |
| `fallback_point_y` | Y coordinate for fallback |
| `withdraw_threshold_percent` | Auto‑retreat morale percent |
| `morale` | Current morale 0‑100 |
| `status` | `'active'`, `'retreating'`, etc. |
| `visible_enemies` | JSON cache for fog of war |
| `issued_by` | UUID of the commander issuing the order |
| `created_at` | When this movement was created |
| `last_updated` | Last time position or status changed |

## Usage

### Inserting orders
When a battle starts or a pre‑plan is finalized, create rows for each unit:
```sql
INSERT INTO public.unit_movements (
  war_id, kingdom_id, unit_type, unit_level, quantity,
  position_x, position_y, stance, movement_path,
  patrol_zone, target_priority, fallback_point_x, fallback_point_y,
  withdraw_threshold_percent, morale, status, issued_by
) VALUES (...);
```

### During each tick
The battle engine updates position, morale and visible enemies:
```sql
UPDATE public.unit_movements
SET position_x = :x,
    position_y = :y,
    morale = morale - :loss,
    last_updated = now()
WHERE movement_id = :id;
```

Use `visible_enemies` to maintain fog‑of‑war caching.

This table powers live battle visualization and replay. Never delete rows while a war is active.

## Best Practices
- Add an index on `war_id` to speed up retrieval of all movements for a battle.
