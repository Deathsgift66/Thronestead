# Troop System Overview

This document explains how unit training, experience and morale interact in **Thronestead**.
It references the core tables that store troop information.

## 1. Unit Tiers and Prerequisites

The `training_catalog` table defines each unit and its requirements.

| Column | Purpose |
| --- | --- |
| `tier` | Progression tier, 1 being the lowest |
| `prerequisite_tech` | Technology needed to unlock training |
| `prerequisite_castle_level` | Minimum castle level |

Example query to list units available at castle level 3:

```sql
SELECT unit_name, tier
FROM training_catalog
WHERE prerequisite_castle_level <= 3
  AND (prerequisite_tech IS NULL OR prerequisite_tech IN (
      SELECT tech_code FROM kingdom_tech WHERE kingdom_id = :kid
  ));
```

## 2. Training Flow

Troop production moves through three tables:

1. **training_queue** – active and pending batches with `xp_per_unit` for each order.
2. **training_history** – completed batches; records `xp_awarded` total.
3. **kingdom_troops** – live troop counts and `unit_xp` for each stack.

When a queue item finishes, move its quantity to `kingdom_troops` and insert a row into `training_history`.

```sql
-- Finish a batch
INSERT INTO training_history (kingdom_id, unit_id, unit_name, quantity, xp_awarded)
SELECT kingdom_id, unit_id, unit_name, quantity, xp_per_unit * quantity
FROM training_queue
WHERE queue_id = :qid;

UPDATE kingdom_troops
SET quantity = quantity + :qty, in_training = in_training - :qty
WHERE kingdom_id = :kid AND unit_type = :unit AND unit_level = 1;

DELETE FROM training_queue WHERE queue_id = :qid;
```

## 3. Experience and Levels

Troops earn experience from training and combat.

- **training_queue.xp_per_unit** – base XP granted per unit on completion.
- **training_history.xp_awarded** – total XP given for that batch.
- **kingdom_troops.unit_xp** – accumulated XP for a troop stack.

When `unit_xp` crosses a threshold, increment `unit_level` and apply bonuses such as increased `damage_bonus` or `morale_bonus`.

```sql
UPDATE kingdom_troops
SET unit_level = unit_level + 1,
    unit_xp = unit_xp - :threshold,
    damage_bonus = damage_bonus + 1
WHERE kingdom_id = :kid AND unit_type = :unit;
```

## 4. Morale Updates

Battle outcomes recorded in `combat_logs` include a `morale_shift` value. Apply this to the stack's morale and update `kingdom_troop_slots` for global modifiers.

Relevant columns in `kingdom_troop_slots`:

- `morale_bonus_buildings`
- `last_morale_update`

```sql
UPDATE kingdom_troops
SET last_morale = GREATEST(0, LEAST(100, last_morale + :shift))
WHERE kingdom_id = :kid AND unit_type = :unit;

UPDATE kingdom_troop_slots
SET last_morale_update = NOW()
WHERE kingdom_id = :kid;
```

## 5. Support and Siege Units

The `unit_stats` table designates special roles:

| Flag | Effect |
| --- | --- |
| `is_support` | Provides buffs or healing; usually cannot capture tiles |
| `is_siege` | Large units that move slowly |
| `can_damage_castle` | Required to harm walls or castles |

```sql
SELECT unit_type, is_support, is_siege, can_damage_castle
FROM unit_stats
WHERE unit_type IN ('healer', 'catapult');
```

These flags inform combat logic and UI restrictions.
