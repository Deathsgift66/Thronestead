# Kingdom Projects Catalogue

The `project_player_catalogue` table defines every kingdom level project available to players. Game designers edit this catalogue to balance construction times, costs and effects. Players never modify rows in this table directly; their progress is tracked in `projects_player`.

## Table Structure

| Column | Purpose / Usage |
| --- | --- |
| `project_code` | Unique project identifier. Primary key. |
| `name` | Name shown in the UI. |
| `description` | Description of the project. |
| `power_score` | Contribution towards power score leaderboards. |
| `cost` | Resource costs stored as `jsonb`. |
| `modifiers` | Bonuses granted when active (json payload). |
| `category` | Project type such as `military`, `economic`, or `support`. |
| `is_repeatable` | If more than one instance can be built. |
| `prerequisites` | Array of prerequisite project/tech codes. |
| `unlocks` | Array of codes unlocked on completion. |
| `build_time_seconds` | Seconds required to construct. |
| `project_duration_seconds` | How long the effect lasts. `NULL` means permanent. |
| `requires_kingdom_level` | Minimum kingdom level required. |
| `is_active` | Whether the project is available for players. |
| `max_active_instances` | Maximum concurrent instances allowed. |
| `required_tech` | Array of tech codes required to unlock. |
| `requires_region` | Optional region restriction. |
| `effect_summary` | Short tooltip text describing the effect. |
| `expires_at` | When the project becomes unavailable. |
| `created_at` | Row creation timestamp. |
| `last_updated` | Timestamp of last edit. |
| `user_id` | Admin user who created the row. |
| `last_modified_by` | Admin who last modified this row. |

## Usage

### Displaying the projects menu

Fetch active projects for display:
```sql
SELECT *
FROM public.project_player_catalogue
WHERE is_active = true
  AND (expires_at IS NULL OR expires_at > now());
```
Show each project's name, description, category, cost, build time and requirements.

### Starting a project
1. Validate requirements:
   - `requires_kingdom_level`
   - prerequisites array
   - `is_repeatable` and `max_active_instances`
2. Deduct the `cost` from `kingdom_resources`.
3. Insert a row into `projects_player`:
```sql
INSERT INTO projects_player (kingdom_id, project_code, starts_at, ends_at)
VALUES (?, ?, now(), now() + (build_time_seconds * interval '1 second'));
```
4. Mark the project as under construction in the UI.

### Completion effects
When `ends_at` is reached apply the `modifiers` json to the player's stats and mark the project as active in `projects_player`.

This catalogue acts as the master list of kingdom projects and should be consulted whenever validating or displaying player projects.
