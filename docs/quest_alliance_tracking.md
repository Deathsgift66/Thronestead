# Alliance Quest Tracking

The `quest_alliance_tracking` table records the live progress of every quest an alliance has started. Each row represents a single instance of a quest for one alliance.

## Purpose
* Show which quests are active or completed for an alliance.
* Track progress and attempt counts for repeatable quests.
* Store timing information for quest expiration.

## Table Structure

| Column | Description |
| --- | --- |
| `alliance_id` | Alliance doing the quest. |
| `quest_code` | Quest identifier from `quest_alliance_catalogue`. |
| `status` | `active` or `completed`. |
| `progress` | Current progress toward the goal. |
| `ends_at` | When this quest ends or expires. |
| `started_at` | Timestamp when the quest was started. |
| `last_updated` | Timestamp of last progress update. |
| `attempt_count` | Number of times this alliance has completed the quest. |
| `started_by` | User who started the quest. |

## Usage

### Starting a quest
```sql
INSERT INTO public.quest_alliance_tracking (
  alliance_id,
  quest_code,
  status,
  progress,
  ends_at,
  started_by
) VALUES (
  :alliance_id,
  :quest_code,
  'active',
  0,
  now() + interval '48 hours',
  :user_id
);
```

### Updating progress
```sql
UPDATE public.quest_alliance_tracking
SET progress = progress + :amount,
    last_updated = now()
WHERE alliance_id = :aid
  AND quest_code = :qcode;
```

### Marking completion
```sql
UPDATE public.quest_alliance_tracking
SET status = 'completed',
    last_updated = now(),
    attempt_count = attempt_count + 1
WHERE alliance_id = :aid
  AND quest_code = :qcode;
```

Expired quests should be cleaned up or marked as such when `now()` exceeds `ends_at`.
