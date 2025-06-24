# Alliance Wars

This table stores the master record for each alliance war. It defines which alliances are involved, the current phase, castle HP, battle tick and overall war status. Other tables such as participants, combat logs, scores and pre-plans all reference this ID.

## Table Structure

| Column | Meaning |
| --- | --- |
| `alliance_war_id` | Unique war ID (primary key) |
| `attacker_alliance_id` | Which alliance is the attacker |
| `defender_alliance_id` | Which alliance is the defender |
| `phase` | War phase: `alert`, `planning`, `live`, `resolved`, etc. (enum: `war_phase`) |
| `castle_hp` | Current HP of the defending alliance's castle |
| `battle_tick` | Current battle tick (advances each battle loop / timer) |
| `war_status` | War status: `active`, `ended`, `cancelled`, etc. (enum: `war_status`) |
| `start_date` | When war started |
| `end_date` | When war ended (NULL if not ended yet) |

## Usage

### Starting a new war
```sql
INSERT INTO alliance_wars (
    attacker_alliance_id, defender_alliance_id, phase, war_status
) VALUES (
    :attacker_id, :defender_id, 'alert', 'active'
)
RETURNING alliance_war_id;
```

### Progressing the war
```sql
UPDATE alliance_wars
SET battle_tick = battle_tick + 1,
    castle_hp = :new_castle_hp
WHERE alliance_war_id = :war_id;
```

### Changing phase
```sql
UPDATE alliance_wars
SET phase = 'live'
WHERE alliance_war_id = :war_id;
```

### Ending a war
```sql
UPDATE alliance_wars
SET war_status = 'ended',
    phase = 'resolved',
    end_date = now()
WHERE alliance_war_id = :war_id;
```

### Querying from the frontend
```sql
SELECT phase, castle_hp, battle_tick, war_status, start_date, end_date
FROM alliance_wars
WHERE alliance_war_id = :war_id;
```

## Why ON DELETE CASCADE
If an alliance is deleted, its wars will be automatically removed. This keeps the database clean with no orphaned wars.

## Indexes
- `attacker_alliance_id` index → fast lookup of wars initiated by an alliance
- `defender_alliance_id` index → fast lookup of wars where an alliance is defending

In short, this table represents **the central control record for each alliance war** and should be referenced by all combat, UI and progress tracking.

