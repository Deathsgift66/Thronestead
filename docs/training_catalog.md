# Training Catalog

The `training_catalog` table defines the base cost and time to train every unit. Records here are referenced by `training_queue` and `training_history` when tracking troop production.

## Table Structure

| Column | Description |
| --- | --- |
| `unit_id` | Primary key for the unit entry |
| `unit_name` | Display name of the unit |
| `tier` | Tech progression tier |
| `training_time` | Base training time in seconds |
| `cost_wood` | Wood required to train one unit |
| `cost_stone` | Stone required |
| `cost_iron_ore` | Iron ore required |
| `cost_gold` | Gold required |
| `cost_gems` | Gems required |
| `cost_food` | Food required |
| `cost_coal` | Coal required |
| `cost_livestock` | Livestock required |
| `cost_clay` | Clay required |
| `cost_flax` | Flax required |
| `cost_tools` | Tools required |
| `cost_wood_planks` | Wood planks required |
| `cost_refined_stone` | Refined stone required |
| `cost_iron_ingots` | Iron ingots required |
| `cost_charcoal` | Charcoal required |
| `cost_leather` | Leather required |
| `cost_arrows` | Arrows required |
| `cost_swords` | Swords required |
| `cost_axes` | Axes required |
| `cost_shields` | Shields required |
| `cost_armour` | Armour pieces required |
| `cost_wagon` | Wagons required |
| `cost_siege_weapons` | Siege weapons required |
| `cost_jewelry` | Jewelry required |
| `cost_spear` | Spears required |
| `cost_horses` | Horses required |
| `cost_pitchforks` | Pitchforks required |

All cost columns default to `0` if not specified.

Initial units are populated via the migration
`migrations/2025_06_29_seed_training_catalog.sql`.
