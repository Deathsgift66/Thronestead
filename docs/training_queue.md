# Training Queue

The `training_queue` table tracks active and pending troop training orders for a player's kingdom.
Each row represents one batch of units that are currently training or waiting to train.

## Table Structure

| Column | Purpose / Usage |
| --- | --- |
| `queue_id` | Unique batch id |
| `kingdom_id` | The player's kingdom training the units |
| `unit_id` | Reference to `training_catalog.unit_id` |
| `unit_name` | Display name of the unit |
| `quantity` | How many units in this batch |
| `training_ends_at` | When training will complete |
| `started_at` | When training began |
| `status` | `queued`, `training`, `paused`, `completed`, `cancelled` |
| `training_speed_modifier` | Modifier applied to training time |
| `modifiers_applied` | JSON of special bonuses applied |
| `initiated_by` | User who started the training |
| `priority` | Higher values train first |
| `last_updated` | Audit timestamp |

## Usage

### Insert a new training batch

```sql
INSERT INTO public.training_queue (
    kingdom_id, unit_id, unit_name, quantity,
    training_ends_at, started_at, status,
    training_speed_modifier, modifiers_applied,
    initiated_by, priority
) VALUES (
    ?, ?, ?, ?,
    now() + (? * ?) * interval '1 second', now(), 'queued',
    ?, ?,
    ?, 1
);
```

### Load a kingdom's queue

```sql
SELECT * FROM public.training_queue
WHERE kingdom_id = ?
  AND status IN ('queued', 'training')
ORDER BY priority DESC, started_at ASC;
```

### Mark a batch complete

```sql
UPDATE public.training_queue
SET status = 'completed', last_updated = now()
WHERE queue_id = ?;
```

### Cancel a batch

```sql
UPDATE public.training_queue
SET status = 'cancelled', last_updated = now()
WHERE queue_id = ? AND kingdom_id = ?;
```

Completed batches should be processed into `kingdom_troops` and then removed from this table.
