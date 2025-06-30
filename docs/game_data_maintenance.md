# Game Data Maintenance

Periodic tasks keep tables like `kingdom_resources` and `spy_missions` consistent.

## Weekly Resource Verification

Run `scripts/game_maintenance.py` once per week. It calls `verify_kingdom_resources` which
ensures every kingdom has a row in `kingdom_resources`.

## Zombie Data Cleanup

The same script removes stale entries from `training_queue` and marks old
`spy_missions` as failed.

Example cron entry:

```cron
0 2 * * 0 /usr/bin/python /path/to/repo/scripts/game_maintenance.py
```
