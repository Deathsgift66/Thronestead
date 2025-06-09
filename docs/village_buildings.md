# Village Buildings

The `village_buildings` table tracks construction progress and building levels within a player's village. It supports queued upgrades, pause/resume and stores audit details.

## Purpose

* Track which buildings exist in each village and their current level.
* Record timestamps for construction start and completion.
* Apply temporary modifiers from events or alliance tech.
* Provide auditability via `constructed_by` and `last_updated`.

## Table Structure

| Column | Description |
| --- | --- |
| `village_id` | Foreign key to the village this building belongs to. |
| `building_id` | Foreign key to `building_catalogue`. |
| `level` | Current level of the building. |
| `construction_started_at` | Timestamp when construction or upgrade started. |
| `construction_ends_at` | Expected end time of the build. |
| `is_under_construction` | Legacy boolean flag (use `construction_status`). |
| `created_at` | When the row was created. |
| `last_updated` | Last time this record was modified. |
| `constructed_by` | UUID of the user who initiated the construction. |
| `active_modifiers` | JSON of buffs or debuffs applied. |
| `construction_status` | `idle`, `queued`, `under_construction`, `paused`, `complete`. |

## Usage

### Viewing current buildings
```sql
SELECT *
FROM public.village_buildings
WHERE village_id = ?;
```

### Starting construction
```sql
INSERT INTO public.village_buildings (
  village_id, building_id, level,
  construction_started_at, construction_ends_at,
  construction_status, constructed_by, is_under_construction
) VALUES (
  ?, ?, ?, now(),
  now() + INTERVAL 'X seconds',
  'under_construction', ?, true
) ON CONFLICT (village_id, building_id)
DO UPDATE SET
  construction_started_at = EXCLUDED.construction_started_at,
  construction_ends_at = EXCLUDED.construction_ends_at,
  construction_status = 'under_construction',
  is_under_construction = true;
```

### Completing construction
```sql
UPDATE public.village_buildings
SET level = level + 1,
    construction_status = 'complete',
    is_under_construction = false,
    last_updated = now()
WHERE village_id = ? AND building_id = ?
  AND now() >= construction_ends_at;
```

### Pause / Resume
```sql
-- Pause
UPDATE public.village_buildings
SET construction_status = 'paused'
WHERE village_id = ? AND building_id = ?;

-- Resume
UPDATE public.village_buildings
SET construction_status = 'under_construction',
    construction_ends_at = now() + INTERVAL 'remaining seconds'
WHERE village_id = ? AND building_id = ?;
```

Buildings should never be deleted. Set `level` to `0` or mark them inactive if needed.
