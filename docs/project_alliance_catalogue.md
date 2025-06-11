# Alliance Project Catalogue

The `project_alliance_catalogue` table defines every Alliance Project available in the game. It acts as the master list that other tables reference whenever an alliance starts a project.

### Purpose

* Acts as a static catalogue managed by admins.
* Each project describes how to unlock it, what it costs and what modifiers it provides.
* Alliances reference a project via the `project_key` value.

## Table Structure

| Column | Purpose |
| --- | --- |
| `project_id` | Serial primary key. |
| `project_key` | Short unique string identifier. |
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

### Column breakdown

* `project_id` – internal serial primary key.
* `project_key` – stable external identifier used by other tables.
* `project_name` – display name in the UI.
* `description` – long description of the project.
* `category` – grouping for the UI such as economic, military or diplomatic.
* `required_tech` – list of tech codes required before starting.
* `prerequisites` – list of other projects that must already be completed.
* `resource_costs` – JSON object describing the alliance vault resources needed.
* `build_time_seconds` – number of seconds the build queue runs.
* `project_duration_seconds` – if set, how long the modifiers remain active.
* `modifiers` – JSON payload of bonuses or effects granted when completed.
* `requires_alliance_level` – minimum alliance level allowed to start.
* `is_active` – indicates if the catalogue entry is currently buildable.
* `is_repeatable` – whether a project can be built more than once.
* `max_active_instances` – cap on simultaneous active copies.

## Usage

### Integration workflow

1. **Load catalogue** – `/alliance/projects` fetches rows where `is_active = true` and shows lock status based on `requires_alliance_level`.
2. **Start project** – validate prerequisites and available resources, then insert into `projects_alliance` with `start_time`, `build_state` of `queued` and the user who initiated the build.
3. **Track build** – periodically calculate `end_time = start_time + build_time_seconds` and move the row to `completed` when the timer ends.
4. **Apply modifiers** – for completed rows marked active (and not expired) merge the `modifiers` JSON into alliance stats or caches.
5. **Handle expiration** – if `project_duration_seconds` is not null compute an `expires_at` timestamp and mark the project `expired` after that time.
6. **List history** – allow UI pages for active and expired projects using the same catalogue data for descriptions.

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

Typical modifiers include bonuses to training speed, additional vault capacity, attack or defense perks in wars, diplomatic bonuses or tax efficiencies.

## Best Practices

* Only admins may modify this catalogue.
* Validate prerequisites before starting a project.
* Log starts and completions in alliance history.
* Periodically clean up expired projects.
* Use `effect_summary` in the UI, but rely on the `modifiers` JSON for calculations.
