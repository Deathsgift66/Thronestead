# public.terrain_map — Codex Integration Guide

🏛 **Purpose**

The `terrain_map` table stores the entire tactical battlefield grid. It is used for:

- Movement and pathfinding
- Unit visibility and fog of war
- Obstacles and terrain features
- Replay of historical battles (same map re-used)
- Map editing, admin tools and procedural map generation

## How Codex should use this table

### 1️⃣ Starting a new war
1. **Check if a map already exists**
   ```sql
   SELECT * FROM public.terrain_map WHERE war_id = ?;
   ```
   If no row is returned, proceed to generate and insert a new map.
2. **Generate and insert map**
   ```sql
   INSERT INTO public.terrain_map (
       war_id, tile_map, map_width, map_height, map_seed, map_version,
       generated_by, map_name, map_type, tile_schema_version, map_source, map_features
   ) VALUES (
       ?, '{ "tiles": [...] }', 20, 60, 123456, 1,
       'uuid-...', 'Battle of Ironfields', 'battlefield', 1, 'auto-generated', '{}'
   );
   ```

### 2️⃣ During battle execution
At the start of each battle (or each tick) load the map:
```sql
SELECT tile_map, map_width, map_height, map_version, tile_schema_version
FROM public.terrain_map
WHERE war_id = ?;
```
Use the result to:
- Load the full tile grid
- Set battlefield dimensions
- Respect tile versioning
- Apply any `map_features` modifiers

### 3️⃣ During battle replay
```sql
SELECT tile_map, map_width, map_height, map_features
FROM public.terrain_map
WHERE war_id = ?;
```
This guarantees replays remain consistent even years later.

### 4️⃣ Admin tools
- View all active maps:
  ```sql
  SELECT * FROM public.terrain_map WHERE is_active = true;
  ```
- Filter by type:
  ```sql
  SELECT * FROM public.terrain_map WHERE map_type = 'siege';
  ```
- Re-use a map:
  ```sql
  UPDATE public.terrain_map SET war_id = ? WHERE terrain_id = ?;
  ```

## Column-by-column usage
| Column | Purpose / How Codex should use |
| --- | --- |
| `terrain_id` | PK, internal use |
| `war_id` | FK → `wars_tactical.war_id` — each battle has one map |
| `tile_map` | Full grid of tiles (terrain type, passability, etc.) |
| `generated_at` | When the map was generated |
| `map_width` / `map_height` | Explicit battlefield size (do **not** infer from `tile_map`) |
| `map_seed` | RNG seed used for procedural generation |
| `map_version` | Version of overall map format |
| `generated_by` | User/admin who created the map |
| `map_name` | Display name for UI / re-use |
| `last_updated` | Audit trail for admin edits |
| `map_type` | Type of battle (`battlefield`, `siege`, `skirmish`, etc.) |
| `tile_schema_version` | Version of the tile JSON format |
| `is_active` | Toggle for retired maps (used by admin tools) |
| `map_source` | How this map was generated (`auto-generated`, `imported`, `custom`, etc.) |
| `map_features` | Global modifiers for the battle engine |

Example `map_features` JSON:
```json
{
  "river_tiles": 12,
  "bridges": 2,
  "has_mountains": true,
  "visibility_penalty_forest": 2,
  "movement_penalty_swamp": 3,
  "global_morale_bonus": 5
}
```
Codex must apply these modifiers when resolving battles.

## Integration steps
| When | Action |
| --- | --- |
| New war created | Check if map exists, else `INSERT` new |
| Battle engine start | `SELECT` full map by `war_id` |
| Each battle tick | Use cached `tile_map` + features |
| Replay | `SELECT` full map by `war_id` |
| Admin map browser | `SELECT *` where `is_active` = true |
| Admin retires map | `UPDATE is_active = false` |

## Codex Best Practices
- **Never delete maps** → always preserve replayability.
- **Always** use `map_width` and `map_height`; do not infer size from `tile_map` alone.
- Always respect `tile_schema_version`:
  ```sql
  SELECT tile_schema_version FROM public.terrain_map WHERE war_id = ?;
  ```
  This allows future upgrades of the tile JSON format.
- If using a procedural generator, always store `map_seed`.
- Record `map_source` for analytics:
  | Source | Meaning |
  | --- | --- |
  | `auto-generated` | Created by the map generator |
  | `custom` | Manually designed |
  | `imported` | From external source |
  | `event` | For special events |

## Final Summary for Codex
| Feature | How to use |
| --- | --- |
| Purpose | Stores full battlefield for a war |
| Used in | Battle engine, replay engine, admin tools |
| Linked to | `wars_tactical.war_id` |
| How to load | `SELECT *` WHERE `war_id` = ? |
| How to update | `INSERT` on new war, `UPDATE` by admin only |
| Key columns | `tile_map`, `map_width`, `map_height`, `tile_schema_version`, `map_features` |

