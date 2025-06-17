# Spy Attack Counter Reset

The `kingdom_spies` table tracks two daily counters:

- `daily_attacks_sent`
- `daily_attacks_received`

These values are used to limit the number of spy attacks a kingdom can perform or
receive each day. A simple cron job resets both counters to `0` every 24 hours.

## Script

Run the script `scripts/reset_spy_attacks.py` once per day. It performs a single
SQL update on `kingdom_spies` and prints how many rows were affected.

Example cron entry:

```cron
0 3 * * * /usr/bin/python /path/to/repo/scripts/reset_spy_attacks.py
```

Adjust the schedule and Python path as needed for your environment.
