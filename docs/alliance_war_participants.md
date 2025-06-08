# Alliance War Participants

This table lists every kingdom involved in a given alliance war and indicates whether they fight on the attacker or defender side.

## Table Structure

| Column | Meaning |
| --- | --- |
| `alliance_war_id` | Which alliance war this participant belongs to |
| `kingdom_id` | Which kingdom is participating |
| `role` | `'attacker'` or `'defender'` |

## Usage

### Starting a war
Add all kingdoms from the attacking and defending alliances:
```sql
INSERT INTO alliance_war_participants (alliance_war_id, kingdom_id, role)
VALUES (:war_id, :kingdom_id, 'attacker');
```

### Adding reinforcements
If additional kingdoms join mid‑war, insert new rows in the same manner.

### Running the battle engine
Retrieve participants by side:
```sql
SELECT kingdom_id
FROM alliance_war_participants
WHERE alliance_war_id = :war_id AND role = 'attacker';
```

### Displaying the war UI
List all attackers and defenders based on this table. It allows the UI to show contributions and which kingdoms are fighting for each side.

### Cleanup and indexing
Participants are removed automatically if the `alliance_wars` record is deleted (`ON DELETE CASCADE`). Indexes on `alliance_war_id` enable fast lookups.

In short, `alliance_war_participants` answers the question **"who is fighting in this alliance war".**
