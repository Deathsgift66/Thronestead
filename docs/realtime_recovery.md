# Real-Time Recovery Tasks

Periodic maintenance keeps time-sensitive tables accurate. The script
`scripts/realtime_recovery.py` finalizes overdue training orders and
marks stale unit movements as defeated.

- `finalize_overdue_training` completes any `training_queue` rows where
  `training_ends_at` is past.
- `fallback_on_idle_training` completes orders that have not updated for
  over an hour.
- `mark_stale_engaged_units_defeated` changes `unit_movements` stuck in
  `engaged` status to `defeated` after 15 minutes of inactivity.

Run the script every few minutes via cron:

```cron
*/5 * * * * /usr/bin/python /path/to/repo/scripts/realtime_recovery.py
```
