# Alliance War Pre-Plans

This table stores each participating kingdom's submitted pre-plan for an alliance war. Pre-plans are edited during the Pre-Planning Phase before live combat begins and are read by the battle engine to initialize units when the war starts.

## Table Structure

| Column | Meaning |
| --- | --- |
| `preplan_id` | Unique row ID |
| `alliance_war_id` | Which alliance war this preplan is for |
| `kingdom_id` | Which kingdom this preplan belongs to |
| `preplan_jsonb` | The actual preplan data (JSONB) containing troop positions, orders, fallback points and priorities |
| `last_updated` | Timestamp of the last edit |

## Usage

### Loading an existing plan
```sql
SELECT preplan_jsonb
FROM alliance_war_preplans
WHERE alliance_war_id = :war_id
  AND kingdom_id = :kingdom_id;
```
If no record exists the client should create an empty plan.

### Saving a plan
```sql
INSERT INTO alliance_war_preplans
  (alliance_war_id, kingdom_id, preplan_jsonb, last_updated)
VALUES
  (:war_id, :kingdom_id, :jsonb_data, now())
ON CONFLICT (alliance_war_id, kingdom_id) DO UPDATE
  SET preplan_jsonb = EXCLUDED.preplan_jsonb,
      last_updated = now();
```

### Loading all plans for battle start
```sql
SELECT kingdom_id, preplan_jsonb
FROM alliance_war_preplans
WHERE alliance_war_id = :war_id;
```

Foreign keys reference `alliance_wars` and `kingdoms` and should cascade on delete so pre-plans are cleaned up if the war is removed. Indexes on `alliance_war_id` and `(alliance_war_id, kingdom_id)` are recommended for fast lookups.

In short, this table represents "each kingdom's submitted war plan for an alliance war".
