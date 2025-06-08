# Alliance Quest Contributions

This table logs every resource, item or special action players contribute toward alliance quests. Each entry represents a single transaction so progress can be audited and displayed in leaderboards.

## Table Structure

| Column | Purpose |
| --- | --- |
| `contribution_id` | Serial primary key |
| `alliance_id` | Which alliance received the contribution |
| `player_name` | Display name at the time of contribution |
| `resource_type` | Resource enum or item type |
| `amount` | Amount contributed |
| `timestamp` | When the contribution occurred |
| `quest_code` | Quest being contributed toward |
| `user_id` | Player UUID for joins and ranking |
| `contribution_type` | `resource`, `item`, `event`, `manual` |

### Example Insert

```sql
INSERT INTO public.quest_alliance_contributions (
  alliance_id,
  player_name,
  resource_type,
  amount,
  timestamp,
  quest_code,
  user_id,
  contribution_type
) VALUES (
  1,
  'PlayerOne',
  'wood',
  500,
  now(),
  'QST_BLD_001',
  '00000000-0000-0000-0000-000000000001',
  'resource'
);
```

### Contribution Log Query

Fetch recent contributions for a quest:

```sql
SELECT player_name, resource_type, amount, timestamp
FROM public.quest_alliance_contributions
WHERE alliance_id = :alliance_id
  AND quest_code = :quest_code
ORDER BY timestamp ASC;
```

### Leaderboard Query

```sql
SELECT user_id, player_name, SUM(amount) AS total_contributed
FROM public.quest_alliance_contributions
WHERE alliance_id = :alliance_id
  AND quest_code = :quest_code
GROUP BY user_id, player_name
ORDER BY total_contributed DESC;
```
