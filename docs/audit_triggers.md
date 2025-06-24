# Audit Triggers

The backend records automatic audit entries whenever certain core tables change.
The `wars`, `combat_logs`, and `training_history` tables now fire triggers that
insert a row into `audit_log` after every insert, update or delete.

Each trigger writes:

- `action` — formatted as `<table>_insert`, `<table>_update` or `<table>_delete`.
- `details` — a short message containing the primary key of the affected row.
- `user_id` and `kingdom_id` when those columns exist on the table (e.g.
  `submitted_by` on `wars` or `trained_by` on `training_history`).

This provides a lightweight audit trail without requiring application code to
manually log these changes.
