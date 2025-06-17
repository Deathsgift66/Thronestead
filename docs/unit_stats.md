# public.unit_stats — Reference

This table defines the core attributes and functional roles for every unit type in **Thronestead**. Combat resolution, troop training and UI previews all read from here.

## Table Structure

| Column | Description |
| --- | --- |
| `unit_type` | Unique ID for the unit (e.g. `archer`) |
| `tier` | Tech progression level (1 basic, 5 advanced) |
| `class` | General type: `infantry`, `ranged`, `cavalry`, `siege`, etc. |
| `description` | Text shown in UI and encyclopedia |
| `hp` | Health pool per unit |
| `damage` | Base attack value |
| `defense` | Reduces incoming damage |
| `speed` | Tiles moved per tick |
| `attack_speed` | Attacks per tick |
| `range` | How many tiles away the unit can hit |
| `vision` | Tiles this unit can reveal |
| `troop_slots` | How many slots this unit consumes |
| `counters[]` | List of unit_types this unit counters |
| `is_siege` | Can damage walls/castles? |
| `is_support` | Provides buffs or debuffs? |
| `icon_path` | Image asset used in the UI |
| `is_visible` | Should this unit appear in troop lists? |
| `base_training_time` | Seconds to train one unit |
| `upkeep_food`, `upkeep_gold` | Cost per tick upkeep |
| `enabled` | Can this unit currently be trained? |
| `last_modified` | Audit field updated on admin edits |
| `can_build_bridge` | Allows pathing modifiers |
| `can_damage_castle` | Needed for siege damage |
| `can_capture_tile` | Can claim tiles during war |
| `special_traits` | JSON field of special behaviours |

## Example Queries

### Show all available units
```sql
SELECT *
FROM unit_stats
WHERE enabled = true AND is_visible = true
ORDER BY tier ASC;
```

### Fetch stats for combat resolver
```sql
SELECT hp, damage, defense, speed, range, attack_speed
FROM unit_stats
WHERE unit_type = 'catapult';
```

### Parse special traits (backend example)
```json
{
  "aoe": true,
  "burn_chance": 0.25,
  "bridge_bonus": 3
}
```

## Best Practices
- Never delete units — set `enabled = false` instead.
- Ensure `unit_type` is consistent across related tables like `training_catalog` and `kingdom_troops`.
- Balance combat and training from this table rather than hard coding values.
- Update `last_modified` on any admin panel edit.
- Use `can_capture_tile` when filtering units that can win wars.
