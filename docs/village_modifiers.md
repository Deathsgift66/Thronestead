# public.village_modifiers — Codex Integration Guide

The `village_modifiers` table stores temporary or permanent bonuses applied to a village. These modifiers adjust resource production, troop effectiveness, construction speed and more. Each row records the origin of the effect and when it expires.

## Table Structure

| Column | Description |
| --- | --- |
| `modifier_id` | Primary key |
| `village_id` | FK to `kingdom_villages.village_id` |
| `resource_bonus` | JSON of resource boosts |
| `troop_bonus` | JSON of combat bonuses |
| `construction_speed_bonus` | Flat percent boost to build speed |
| `defense_bonus` | Defensive bonus when attacked |
| `trade_bonus` | Trade related bonuses |
| `source` | Origin of the modifier (system, event, building, etc.) |
| `stacking_rules` | JSON defining stacking behaviour |
| `expires_at` | When the effect ends (`null` = permanent) |
| `applied_by` | UUID of the user who triggered it |
| `created_at` | Timestamp when applied |
| `last_updated` | Last time the record changed |

## Usage

### Listing active modifiers
```sql
SELECT *
FROM public.village_modifiers
WHERE village_id = ?
  AND (expires_at IS NULL OR expires_at > NOW());
```

### Applying a modifier
```sql
INSERT INTO public.village_modifiers (
  village_id, resource_bonus, troop_bonus,
  source, applied_by, expires_at
) VALUES (...)
ON CONFLICT (village_id, source) DO UPDATE
SET resource_bonus = EXCLUDED.resource_bonus,
    troop_bonus = EXCLUDED.troop_bonus,
    last_updated = NOW();
```

### Cleaning up expired rows
```sql
DELETE FROM public.village_modifiers
WHERE expires_at < NOW();
```

Always check `expires_at` when loading modifiers and respect `stacking_rules` for combined effects.
