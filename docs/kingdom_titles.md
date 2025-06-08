# Kingdom Titles

This table tracks honorary titles earned by each kingdom. Titles are purely cosmetic and used for bragging rights on profiles, leaderboards and war pages.

## Table: `kingdom_titles`

| Column      | Meaning                                   |
|-------------|-------------------------------------------|
| `kingdom_id`| Kingdom that earned the title             |
| `title`     | Name of the title                         |
| `awarded_at`| Timestamp when the title was granted      |

A kingdom can hold multiple titles. Rows should not be removed except by an admin.

### Example insert
```sql
INSERT INTO public.kingdom_titles (kingdom_id, title)
VALUES (123, 'Defender of the Realm');
```

Fetch titles for display:
```sql
SELECT title, awarded_at
FROM public.kingdom_titles
WHERE kingdom_id = ?
ORDER BY awarded_at DESC;
```

## Active Title

Players may select one title to show as their current badge. The `active_title` column on `kingdoms` stores this choice.
