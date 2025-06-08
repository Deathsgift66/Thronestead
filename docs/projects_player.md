# Player Projects

The `projects_player` table tracks every instance of a project that a kingdom has started or completed. Rows are created when a player launches a project from the `project_player_catalogue`.

## Table Structure

| Column | Purpose / Usage |
| --- | --- |
| `project_id` | Unique project instance. Primary key. |
| `kingdom_id` | The player kingdom this project belongs to. |
| `project_code` | FK to `project_player_catalogue.project_code`. |
| `power_score` | Contribution score used for rankings. |
| `starts_at` | Timestamp when the project was started. |
| `ends_at` | When the project finishes (`NULL` if permanent). |
| `build_state` | `queued`, `building`, `completed` or `expired`. |
| `is_active` | Whether the project effects are enabled. |
| `started_by` | User who initiated the project. |
| `last_updated` | Audit timestamp for modifications. |
| `expires_at` | When temporary effects should expire. |

## Usage

### Displaying projects

```sql
SELECT pp.*, pc.name, pc.category, pc.modifiers
FROM projects_player pp
JOIN project_player_catalogue pc ON pp.project_code = pc.project_code
WHERE pp.kingdom_id = ?
  AND (pp.ends_at IS NULL OR pp.ends_at > now())
ORDER BY pp.starts_at DESC;
```

Show each project's name, power score and progress. If `ends_at` has passed mark it as **Completed**.

### Starting a project

```sql
INSERT INTO projects_player (kingdom_id, project_code, power_score, starts_at, ends_at)
VALUES (?, ?, ?, now(), now() + interval 'X seconds');
```

Use the catalogue entry to determine build time, cost and modifiers.

### Completion and expiration

When `ends_at` is reached apply the modifiers from the catalogue. If the project is temporary use `expires_at` to disable its effects later.

## Best Practices

* Prevent duplicates for non-repeatable projects:

```sql
SELECT * FROM projects_player
WHERE kingdom_id = ?
  AND project_code = ?
  AND ends_at > now();
```

* Respect `max_active_instances` for repeatables.
* Sync modifiers to the kingdom upon completion.

## Integration Flow Summary

1. Player starts a project → insert row with start and end timestamps.
2. On game ticks or login check `ends_at` and apply bonuses.
3. Expire temporary projects using `expires_at` and `is_active`.
