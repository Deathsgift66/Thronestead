# Unit Counters

The `unit_counters` table defines which unit types counter others and how effective they are. Codex applies these multipliers during combat and shows them in UI tooltips.

## Table Structure

| Column | Meaning |
| --- | --- |
| `unit_type` | Attacking unit that has the advantage. |
| `countered_unit_type` | Target unit that is countered. |
| `effectiveness_multiplier` | Damage or accuracy multiplier when the counter applies. Defaults to `1.5`. |
| `source` | Where the rule originates (`base`, `event`, `tech`, etc.). |
| `notes` | Optional conditions such as terrain restrictions. |

## Usage

### Combat resolution
```sql
SELECT effectiveness_multiplier
FROM public.unit_counters
WHERE unit_type = :attacker AND countered_unit_type = :defender;
```
Apply the multiplier if a row is returned. If no match exists, use `1.0`.

### UI display
Show counter relationships on unit stat panels so players know which units they are strong or weak against.

### Admin tools
Allow administrators to view and modify these rows. The `source` column enables tech or event based overrides.

## Best Practices
- Keep the table indexed on `(unit_type, countered_unit_type)`.
- Only use multipliers of `1.0` or higher.
- Use the same `unit_type` values found in `unit_stats`.
- Avoid conflicting double bonuses from overlapping rows.

## Example
| unit_type | countered_unit_type | multiplier | source |
| --- | --- | --- | --- |
| `spearman` | `cavalry` | `1.5` | `base` |
| `archer` | `heavy_infantry` | `1.2` | `base` |
| `scout` | `siege_weapons` | `1.3` | `tech` |

