# New Player Onboarding

When a player signs up and completes the onboarding flow (`play.html` & `play.js`), several database records are created to ensure the new kingdom can immediately begin play.

1. **users** – A profile row with `setup_complete` marked `true` and the generated `kingdom_id`.
2. **kingdoms** – The core kingdom record containing the chosen name and region.
3. **villages** – The first village associated with the kingdom.
4. **kingdom_resources** – Resource ledger populated with the region's bonus values.
5. **kingdom_troop_slots** – Starting troop slot count of `20` plus any regional bonus.

Additional tables such as `kingdom_castle_progression` are initialized lazily on first access by the progression API.
