# Progression System

This subsystem tracks castle level, nobles and knights. Progress is stored
in PostgreSQL tables accessed through SQLAlchemy. The helper functions in
`services/progression_service.py` aggregate troop slot bonuses for a kingdom and
provide reusable validation helpers.

* `calculate_troop_slots(kid)` – aggregate base and bonus slots
* `check_progression_requirements(kid, castle, nobles, knights)` – raise an
  HTTP 403 error if the given kingdom does not meet the required castle level or
  unit counts
* `check_troop_slots(kid, troops_requested)` – raise an HTTP 400 error when a
  troop training request would exceed the available slots

## Castle Progression
Castle upgrades require resources. When costs are paid the castle level increases.

## Nobles Management
- Nobles are represented as a list of names.
- You can add or remove nobles through the API.

## Knights Management
- Knights are stored in a dictionary of `id -> {"rank": int}`.
- New knights can be added with an initial rank.
- Knights can be promoted which increases their rank.

See `docs/progression.postman_collection.json` or `docs/progression_curl_examples.md` for example API usage.
