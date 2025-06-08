# Alliance Project Catalogue

The `project_alliance_catalogue` table defines every Alliance Project available in the game. It is static data maintained by admins and referenced whenever an alliance chooses a project to start.

## Table Structure

| Column | Purpose |
| --- | --- |
| `project_code` | Short unique string identifier (primary key). |
| `project_name` | Name shown to players. |
| `description` | Detailed description. |
| `category` | Project category such as `Military`, `Economic`, `Diplomatic`, `Special`. |
| `effect_summary` | Short summary for the UI. |
| `is_repeatable` | Can this project be repeated? |
| `required_tech` | Array of tech codes required to unlock. |
| `prerequisites` | Array of other projects that must be completed first. |
| `unlocks` | Array of projects or abilities unlocked by completing this project. |
| `resource_costs` | Resources required to build (jsonb). |
| `build_time_seconds` | Time to build in seconds. |
| `project_duration_seconds` | If temporary, how long the modifiers last. |
| `created_at` | Audit timestamp when created. |
| `last_updated` | Audit timestamp when last modified. |
| `user_id` | Admin user who created/edited the entry. |
| `modifiers` | Bonuses/effects applied when completed (jsonb). |
| `requires_alliance_level` | Minimum alliance level required. |
| `is_active` | Whether this project is currently available. |
| `max_active_instances` | Maximum active instances allowed. |
| `expires_at` | Pre-set expiry date if applicable. |

## Usage

### Listing available projects

```sql
SELECT *
FROM project_alliance_catalogue
WHERE is_active = true
  AND requires_alliance_level <= :alliance_level;
```

### Starting a project

1. Validate `required_tech` and `prerequisites` for the alliance.
2. Deduct `resource_costs` from `alliance_vault`.
3. Insert a row into `projects_alliance` with `starts_at` and `ends_at` calculated from `build_time_seconds`.

### Completion and effects

When a project completes, merge the `modifiers` into the alliance or member stats. If `project_duration_seconds` is set, track an expiry time and remove the effects later.

`is_repeatable` and `max_active_instances` should be enforced so that unique projects cannot be stacked beyond their limits.

## Best Practices

* Only admins may modify this catalogue.
* Validate prerequisites before starting a project.
* Log starts and completions in alliance history.
* Periodically clean up expired projects.
* Use `effect_summary` in the UI, but rely on the `modifiers` JSON for calculations.
