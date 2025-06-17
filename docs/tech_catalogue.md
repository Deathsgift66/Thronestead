# Technology Catalogue

This table defines every research technology available in **Thronestead**. The frontend queries this table to display the tech tree and the backend references it when validating research actions.

| Column | Purpose |
| --- | --- |
| `tech_code` | Unique code used as the primary key. |
| `name` | Display name of the technology. |
| `description` | Short description of the benefits. |
| `category` | Category for filtering (e.g. `espionage`, `food_production`). |
| `tier` | Progression tier from 1 to 5. |
| `duration_hours` | Time in hours required to research. |
| `encyclopedia_entry` | Lore entry unlocked when completed. |
| `modifiers` | JSONB of bonuses applied when completed. |
| `prerequisites` | Array of tech codes required before starting. |
| `required_kingdom_level` | Minimum kingdom level to begin research. |
| `required_region` | Region restriction if any. |
| `is_repeatable` | Whether the tech can be researched multiple times. |
| `max_research_level` | Max level if repeatable. NULL for one-time tech. |
| `is_active` | Set to false to hide deprecated techs. |
| `created_at` / `last_updated` | Audit timestamps. |
| `military_bonus` / `economic_bonus` | Optional numeric bonus fields. |

## Example Seed Data

The `migrations/2025_06_17_populate_tech_catalogue.sql` script provides sample technologies used during development. Run it after `full_schema.sql` to populate the catalogue.

```bash
psql -f full_schema.sql
psql -f migrations/2025_06_17_populate_tech_catalogue.sql
```
