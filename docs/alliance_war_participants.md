# Alliance War Participants

This table records which kingdoms are involved in a specific alliance war and what role they play.

## Purpose
- Track all kingdoms fighting in an alliance war.
- Specify whether each kingdom is on the **attacker** or **defender** side.

## Columns
| Column          | Meaning                                            |
|-----------------|----------------------------------------------------|
| `alliance_war_id` | ID of the alliance war this kingdom is part of     |
| `kingdom_id`      | ID of the participating kingdom                    |
| `role`            | `'attacker'` or `'defender'` indicating the side   |

## Usage
1. **War start:** insert the kingdoms of the attacking and defending alliances.
2. **Reinforcements:** insert additional rows when other kingdoms join mid‑war.
3. **Battle engine:** query kingdoms by role for each war to resolve combat.
4. **War UI:** display all participants to players and tally their contributions.

Rows are automatically removed when an alliance war is deleted thanks to `ON DELETE CASCADE`. An index on `alliance_war_id` speeds up lookups.
