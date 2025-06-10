# public.war_preplans — Codex Integration Guide

This table stores each kingdom's strategic plan for a tactical war. Records are created when a kingdom joins a war and are finalized before combat begins. The battle engine loads only the finalized plans.

## Integration Overview

| Phase | How it's used |
| --- | --- |
| Pre‑War | Insert an empty row for every participating kingdom |
| Planning | Players update `preplan_jsonb` many times as a draft |
| Lock‑In | When finalized set `is_finalized = true` and update `status` |
| Battle Start | Engine selects rows where `is_finalized = true` |
| Replay | Preplans are displayed as the starting state |

## How Codex should use this table

1. **Insert an Initial Preplan**
   ```sql
   INSERT INTO public.war_preplans (war_id, kingdom_id, submitted_by, preplan_jsonb)
   VALUES (?, ?, ?, '{}');
   ```
2. **Save Draft**
   ```sql
   UPDATE public.war_preplans
   SET preplan_jsonb = ?, last_updated = now(), version = version + 1
   WHERE war_id = ? AND kingdom_id = ?;
   ```
3. **Finalize Submission**
   ```sql
   UPDATE public.war_preplans
   SET is_finalized = true, status = 'submitted', last_updated = now()
   WHERE war_id = ? AND kingdom_id = ?;
   ```
4. **Load for Battle Engine**
   ```sql
   SELECT * FROM public.war_preplans
   WHERE war_id = ? AND is_finalized = true;
   ```

## Column-by-Column Explanation

| Column | Description |
| --- | --- |
| `preplan_id` | Primary key, unique per preplan |
| `war_id` | FK to `wars_tactical` — identifies the war |
| `kingdom_id` | FK to `kingdoms` — who submitted the plan |
| `preplan_jsonb` | JSON payload of unit orders, formations and fallback points |
| `created_at` | When the plan was first created |
| `last_updated` | Last time this plan was modified |
| `submitted_by` | FK to `users.user_id` — who submitted the plan |
| `is_finalized` | Marks plan as locked and ready for execution |
| `version` | Integer version to track changes |
| `status` | `'draft'`, `'submitted'`, `'approved'` |

## Recommended JSON Format for `preplan_jsonb`
```json
{
  "formation": "phalanx",
  "fallback_point": { "x": 5, "y": 12 },
  "orders": [
    { "unit": "infantry", "stance": "aggressive", "target": "tile:10x12" },
    { "unit": "archers", "stance": "defensive", "target": "bridge" }
  ],
  "bridge_targets": [12, 15],
  "priority_zones": [
    { "zone": [[10,11],[10,12]], "importance": "high" }
  ]
}
```

## Best Practices

- Enforce one row per kingdom per war
- Use `is_finalized` to lock plans before battle
- Increment `version` on each save for audit history
- Always record `submitted_by` and timestamps for accountability
- Index `war_id` and `kingdom_id` for performance
