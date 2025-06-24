# Kingdom Achievements

This document describes the tables that power kingdom achievements and how they are used in the game.

## Table: `kingdom_achievement_catalogue`
The catalogue is the master list of every possible kingdom achievement.

| Column | Meaning |
| --- | --- |
| `achievement_code` | Unique string ID used to unlock the achievement. |
| `name` | Display name shown in the UI. |
| `description` | Description of the requirement. |
| `category` | Grouping (`military`, `economic`, `diplomatic`, `exploration`, `infrastructure`). |
| `reward` | JSON payload describing the reward when earned. |
| `prestige_reward` | Prestige score granted when earned. |
| `is_hidden` | If true, hidden until unlocked. |
| `created_at` | Creation timestamp. |
| `last_updated` | Timestamp of the last modification. |

## Table: `kingdom_achievements`
Records which kingdoms have unlocked which achievements.

| Column | Meaning |
| --- | --- |
| `kingdom_id` | Player's kingdom ID. |
| `achievement_code` | Identifier from the catalogue. |
| `awarded_at` | When the achievement was earned. |

## Usage
1. **Checking triggers** – After relevant player actions, query `kingdom_achievements` to see if the row exists. If not, insert it, fetch the `reward` from `kingdom_achievement_catalogue`, apply it and notify the player.
2. **Achievement page** – The `/kingdom/achievements` page queries all catalogue entries and the player's unlocked ones. Locked achievements marked `is_hidden` are not shown until earned.
3. **Leaderboards** – Sum `prestige_reward` from unlocked achievements per kingdom for ranking.

Unlocking an achievement automatically increases the kingdom's `prestige_score`
by the associated `prestige_reward` and records an `ACHIEVEMENT_UNLOCKED` entry in
`kingdom_history_log`.

Both tables are system managed. Players cannot edit them directly.
