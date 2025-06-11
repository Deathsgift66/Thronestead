# Alliance Projects

The `projects_alliance` table tracks every active or queued Alliance Project. Each row represents a specific instance of a project either being built or already completed.

## Table Purpose

* Stores the runtime state of Alliance Projects.
* Links back to the static `project_alliance_catalogue` via `project_key`.
* Used when displaying `/alliance/projects` and for applying active modifiers.

## Table Structure

| Column | Meaning |
| --- | --- |
| `project_id` | Unique project instance identifier. Primary key. |
| `alliance_id` | Alliance that owns this project. |
| `name` | Project name (duplicated from catalogue). |
| `project_key` | FK to `project_alliance_catalogue.project_key`. |
| `progress` | Current build progress 0-100. |
| `modifiers` | Bonuses applied when active. |
| `start_time` | When construction started. |
| `end_time` | Scheduled completion time. |
| `is_active` | `true` if currently providing bonuses. |
| `build_state` | `queued`, `building`, `completed`, or `expired`. |
| `built_by` | User who initiated the build. |
| `expires_at` | When the effect expires (for temporary projects). |
| `last_updated` | Audit timestamp of last change. |

## Usage

### Listing active projects

```sql
SELECT *
FROM public.projects_alliance
WHERE alliance_id = :aid
  AND (is_active = true OR build_state IN ('queued', 'building'))
ORDER BY start_time DESC;
```

### Starting a project

```sql
INSERT INTO projects_alliance (alliance_id, name, project_key, start_time, build_state, built_by)
VALUES (:aid, :name, :pkey, now(), 'queued', :uid);
```

### Marking as completed

```sql
UPDATE projects_alliance
SET build_state = 'completed',
    is_active = true,
    progress = 100,
    last_updated = now()
WHERE project_id = :pid;
```

Expired projects should be updated to `build_state = 'expired'` and `is_active = false` when `expires_at` is reached.
