# Kingdoms

The `kingdoms` table stores the master record for every player kingdom in the game. Each row represents one player's realm and acts as the anchor for all other kingdom data such as resources, troops, spies and treaties.

## Table: `public.kingdoms`

| Column | Purpose / How to use |
| --- | --- |
| `kingdom_id` | Primary key, unique kingdom ID |
| `user_id` | FK to `users.user_id` — owner of this kingdom |
| `kingdom_name` | Player-chosen name of the kingdom |
| `region` | Region of the world this kingdom belongs to |
| `created_at` | When this kingdom was created |
| `prestige_score` | Overall ranking score (used for leaderboards) |
| `avatar_url` | URL to avatar image |
| `status` | `active`, `inactive`, `banned`, `deleted` — hide inactive kingdoms |
| `description` | Kingdom flavor text (bio) |
| `motto` | Short slogan / motto |
| `ruler_name` | Player-chosen ruler of the kingdom |
| `alliance_id` | FK to `alliances.alliance_id` — if in an alliance |
| `alliance_role` | `leader`, `officer`, `member`, `NULL` if not in alliance |
| `tech_level` | Player’s tech level (affects unlocks) |
| `economy_score` | Sub-score for economy leaderboards |
| `military_score` | Sub-score for military leaderboards |
| `diplomacy_score` | Sub-score for diplomacy leaderboards |
| `last_login_at` | Last time this player was online ("active players") |
| `last_updated` | Sync field — update whenever kingdom info changes |
| `is_npc` | `true` if this is an NPC kingdom |

## Usage Examples

### Creating a new kingdom
```sql
INSERT INTO public.kingdoms (user_id, kingdom_name, region, ruler_name)
VALUES (?, ?, ?, ?);
```

### Fetching the profile page
```sql
SELECT kingdom_name, ruler_name, region, description, motto,
       prestige_score, military_score, economy_score, diplomacy_score,
       avatar_url, status, alliance_id, alliance_role
FROM public.kingdoms
WHERE kingdom_id = ?;
```

### Leaderboard ordering
```sql
SELECT kingdom_name, prestige_score
FROM public.kingdoms
ORDER BY prestige_score DESC;
```

### Alliance roster
```sql
SELECT kingdom_id, kingdom_name, ruler_name, military_score
FROM public.kingdoms
WHERE alliance_id = ? AND status = 'active';
```

### NPC kingdoms
```sql
SELECT kingdom_id, kingdom_name
FROM public.kingdoms
WHERE is_npc = true;
```

This table is the authoritative record for all kingdoms and should be referenced by foreign keys for any new feature.
