# Region Catalogue

This table defines all playable regions in **Kingmakers Rise**. It acts as a static lookup referenced by `kingdoms.region`.

| Column | Purpose |
| --- | --- |
| `region_code` | Short code primary key used by `kingdoms.region` |
| `region_name` | Display name for the region |
| `description` | Lore / flavour text |
| `resource_bonus` | JSONB object of resource production modifiers |
| `troop_bonus` | JSONB object of troop stat modifiers |

## Example Queries

### List regions for selection
```sql
SELECT region_code, region_name, description, resource_bonus, troop_bonus
FROM public.region_catalogue
ORDER BY region_name ASC;
```

### Fetch a kingdom's region details
```sql
SELECT r.region_name, r.description, r.resource_bonus, r.troop_bonus
FROM public.region_catalogue r
JOIN public.kingdoms k ON k.region = r.region_code
WHERE k.kingdom_id = ?;
```

Both bonus columns store percentage modifiers. For example:
```json
{
    "wood": 10,
    "stone": -5,
    "gold": 15
}
```
```json
{
    "infantry_hp": 5,
    "archer_damage": 10,
    "cavalry_speed": -10
}
```

These values are applied dynamically during resource production and troop combat calculations.
