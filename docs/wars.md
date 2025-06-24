# public.wars — Codex Integration Guide

This table tracks every war declared between players or alliances. Records are created whenever a war is declared and remain for auditing even after the conflict ends.

## Table Structure

| Column | Meaning |
| --- | --- |
| `war_id` | Unique war ID |
| `attacker_id` | UUID of the user who started the war |
| `defender_id` | UUID of the user being attacked |
| `attacker_name` | Snapshot of attacker name at declaration |
| `defender_name` | Snapshot of defender name at declaration |
| `war_reason` | Optional text justification |
| `status` | `pending`, `active`, `ended`, `cancelled` |
| `start_date` | When fighting began |
| `end_date` | When the war ended |
| `attacker_score` | Points earned by the attacker |
| `defender_score` | Points earned by the defender |
| `attacker_kingdom_id` | Kingdom initiating the war |
| `defender_kingdom_id` | Kingdom being attacked |
| `war_type` | `duel`, `alliance_war`, `event_war` |
| `is_retaliation` | `true` if the war was a response |
| `treaty_triggered` | Started automatically from a treaty |
| `victory_condition` | `score`, `timed`, `objective`, `mutual_peace` |
| `outcome` | `attacker_win`, `defender_win`, `draw`, `cancelled` |
| `created_at` | Row creation timestamp |
| `last_updated` | Auto updated timestamp |
| `submitted_by` | User who declared the war |

## Usage Patterns
1. **Declaration** – insert a row with `status = 'pending'`.
2. **Activation** – set `status = 'active'` and `start_date = now()` when combat begins.
3. **Completion** – update `status` to `ended` and store scores/outcome.

## Indexes
```
CREATE INDEX IF NOT EXISTS idx_wars_attacker ON public.wars (attacker_id);
CREATE INDEX IF NOT EXISTS idx_wars_defender ON public.wars (defender_id);
CREATE INDEX IF NOT EXISTS idx_wars_status ON public.wars (status);
CREATE INDEX IF NOT EXISTS idx_wars_type ON public.wars (war_type);
```

## Audit Logging

Every insert, update, or delete on this table triggers `trg_wars_audit`, which
creates a descriptive entry in `audit_log`.
