# Spy Missions

This table tracks spy missions that players launch from their kingdoms.

## Table Structure

| Column | Meaning |
| --- | --- |
| `mission_id` | Unique mission ID (primary key) |
| `kingdom_id` | The kingdom that launched the mission |
| `mission_type` | Type of mission (sabotage, intel, etc.) |
| `target_id` | Target identifier depending on mission type |
| `status` | `'active'`, `'success'`, or `'fail'` |
| `launched_at` | When the mission was started |
| `completed_at` | When the mission finished |

## Usage

Launch a mission:
```sql
INSERT INTO spy_missions (kingdom_id, mission_type, target_id, status)
VALUES (1, 'intel', 456, 'active');
```

List active missions:
```sql
SELECT *
FROM spy_missions
WHERE kingdom_id = 1 AND status = 'active'
ORDER BY launched_at DESC;
```

Mark mission complete:
```sql
UPDATE spy_missions
SET status = 'success', completed_at = now()
WHERE mission_id = 7;
```

Fetch recent missions:
```sql
SELECT *
FROM spy_missions
WHERE kingdom_id = 1
ORDER BY launched_at DESC
LIMIT 50;
```
