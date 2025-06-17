# Spy Defense

The `spy_defense` table stores the espionage defense rating for each kingdom. Buildings and research can increase this value to make incoming spy missions more difficult.

## Table Structure

| Column | Meaning |
| --- | --- |
| `kingdom_id` | Associated kingdom |
| `defense_rating` | Total defense points |
| `last_updated` | When the value was last modified |
