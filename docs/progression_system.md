# Progression System

This subsystem tracks castle experience, nobles and knights. Progress is stored
in PostgreSQL tables accessed through SQLAlchemy. The helper functions in
`services/progression_service.py` aggregate troop slot bonuses for a kingdom.

## Castle Progression
- Experience points are gained through various actions.
- When XP reaches 100, the castle level increases and XP resets.

## Nobles Management
- Nobles are represented as a list of names.
- You can add or remove nobles through the API.

## Knights Management
- Knights are stored in a dictionary of `id -> {"rank": int}`.
- New knights can be added with an initial rank.
- Knights can be promoted which increases their rank.

See `docs/progression.postman_collection.json` or `docs/progression_curl_examples.md` for example API usage.
