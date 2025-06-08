# Kingdom History Log

This table stores a chronological history of important events for each player's kingdom. It acts like an activity feed or journal so players can review what has happened over time.

## Table Structure

| Column | Meaning |
| --- | --- |
| `log_id` | Unique row ID |
| `kingdom_id` | Which kingdom the event belongs to |
| `event_type` | Short code describing the event |
| `event_details` | Human readable details displayed to the player |
| `event_date` | Timestamp when the event occurred |

## Usage

Insert a row whenever a significant event occurs:

```sql
INSERT INTO kingdom_history_log (kingdom_id, event_type, event_details)
VALUES (5, 'war_victory', 'Defeated Kingdom of Rivertown');
```

Fetch recent history for display:

```sql
SELECT event_type, event_details, event_date
FROM kingdom_history_log
WHERE kingdom_id = 5
ORDER BY event_date DESC
LIMIT 50;
```

Rows should never be updated or deleted except when a player removes their account.
