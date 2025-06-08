# Alliance Quest Catalogue

The `quest_alliance_catalogue` table defines every quest an alliance can undertake. It acts as the master list used when displaying available quests and when creating rows in `quest_alliance_tracking`.

## Purpose

* Admin-managed catalogue of alliance quests.
* Contains objectives, rewards and gating requirements.
* Entries are referenced via `quest_code`.

## Table Structure

| Column | Purpose |
| --- | --- |
| `quest_code` | Primary key identifier for the quest. |
| `name` | Quest name shown to players. |
| `description` | Long description. |
| `duration_hours` | How long the quest lasts once started. |
| `category` | Quest type such as `combat`, `economic`, `exploration`, etc. |
| `objectives` | JSONB detailing what must be accomplished. |
| `rewards` | JSONB describing rewards granted. |
| `required_level` | Minimum alliance level to unlock. |
| `repeatable` | If `true`, quest can be repeated. |
| `max_attempts` | Maximum attempts allowed if repeatable. `NULL` for unlimited. |
| `is_active` | Set to `false` to hide the quest from the UI. |
| `created_at` | Timestamp when the row was created. |
| `last_updated` | Timestamp when last modified. |

## Usage

### Listing available quests

```sql
SELECT *
FROM public.quest_alliance_catalogue
WHERE is_active = true
  AND required_level <= (SELECT level FROM alliances WHERE alliance_id = :alliance_id);
```

### Starting a quest

```sql
INSERT INTO public.quest_alliance_tracking (alliance_id, quest_code, status, progress, ends_at)
VALUES (:alliance_id, :quest_code, 'active', 0,
        now() + (SELECT duration_hours * interval '1 hour'
                  FROM public.quest_alliance_catalogue WHERE quest_code = :quest_code));
```

### Progress and completion

While active, players contribute resources or complete objectives. Progress is tracked in `quest_alliance_tracking`. Once objectives are met, rewards from the catalogue are processed and the quest marked `completed`.

Only administrators modify this catalogue. Quests should never be deleted—set `is_active` to `false` instead.
