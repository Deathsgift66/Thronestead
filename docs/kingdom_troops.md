# Kingdom Troops

The `kingdom_troops` table stores the live state of a player's military forces. Each row is keyed by `(kingdom_id, unit_type, unit_level)` so troops of the same type can exist at multiple levels. The table tracks healthy, training and wounded soldiers for combat history.

## Table Structure

| Column | Meaning |
| --- | --- |
| `kingdom_id` | Which player kingdom owns these troops |
| `unit_type` | The type of unit (e.g. `Spearman`, `Knight`) |
| `quantity` | How many healthy troops at this level |
| `in_training` | How many are currently being trained |
| `wounded` | How many are wounded (cannot fight) |
| `unit_level` | What level these troops are (1 = base troops) |
| `active_modifiers` | JSON of temporary modifiers (buffs, debuffs, tech bonuses, etc.) |
| `last_modified_by` | Last user/admin/system that updated this row |
| `last_combat_at` | When these troops last fought in a battle |
| `last_morale` | The morale of this troop stack |

## Usage

### Displaying troop list

```sql
SELECT unit_type, unit_level, quantity, in_training, wounded, unit_xp
FROM public.kingdom_troops
WHERE kingdom_id = ?
ORDER BY unit_type, unit_level DESC;
```

### Calculating battle deployment

Use only healthy troops:

```sql
SELECT *
FROM public.kingdom_troops
WHERE kingdom_id = ?
  AND quantity > 0
  AND wounded = 0;
```

### Leveling up troops

1. Subtract quantity from the lower level row.
2. Add that quantity to the next level row (insert if needed).

```sql
-- Lower level
UPDATE public.kingdom_troops
SET quantity = quantity - 10
WHERE kingdom_id = ? AND unit_type = ? AND unit_level = 1;

-- Higher level
INSERT INTO public.kingdom_troops (kingdom_id, unit_type, unit_level, quantity)
VALUES (?, ?, 2, 10)
ON CONFLICT (kingdom_id, unit_type, unit_level)
DO UPDATE SET quantity = kingdom_troops.quantity + 10;
```

### Wounding troops

```sql
UPDATE public.kingdom_troops
SET quantity = quantity - ?, wounded = wounded + ?
WHERE kingdom_id = ? AND unit_type = ? AND unit_level = ?;
```

### Training troops

Use `in_training` while units are in the queue. When training completes, move them into `quantity`.

## Best Practices

This structure supports leveled troops, training queues, wounded recovery, morale tracking, and audit history. Treat updates as critical game state and audit via `last_modified_by`.

