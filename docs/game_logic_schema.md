# Game Logic Schema

This document outlines the major gameplay systems in **Thronestead** and how they interact. It acts as a high-level blueprint for developers.

## 1. Onboarding and Initial State
- When a new player completes signup, records are inserted into multiple tables to set up their kingdom: `users`, `kingdoms`, `villages`, `kingdom_resources`, `kingdom_troop_slots` and `kingdom_nobles` among others. These steps are described in `docs/onboarding_setup.md`.
- This ensures every kingdom begins with core resources, a starter village, troop capacity and a noble to enable progression.

## 2. Progression Loops
- The game advances in stages. Core loops described in `docs/kingdom_progression_stages.md` are:
  - **Primary Loop** — Castle Level → Nobles → Villages → Resources → Troops → Wars → Castle Level increase.
  - **Military Loop** — Castle Level → Knights → Troop Slots → Elite Troops → War Participation → Military Rank increase.
  - **Alliance Loop** — Alliance Membership → Alliance Quests → Alliance Projects → Alliance Wars → Global Rank increase.
  - **Diplomacy Loop** — Nobles → Treaties → War Alliances → Global Politics → Reputation increase.
- These loops inform the dependencies between castle progression, economic growth, military power and diplomatic standing.

## 3. Resource Economy
- Each kingdom has a resource ledger stored in the `kingdom_resources` table. Resources are produced over time and deducted when constructing buildings, training troops or trading.
- Alliance taxes, trades and war loot transfer resources between kingdoms or alliances. See `docs/kingdom_resources.md` for query examples and best practices.

## 4. Troop Training
- The `training_queue` table tracks pending and active batches of units. Each row specifies the unit type, quantity, training duration and status.
- When training completes, units move into `kingdom_troops` where level and wounded counts are tracked.

## 5. Projects and Quests
- Player projects (`projects_player`) and alliance projects (`projects_alliance`) provide modifiers or unlock features when completed. Alliance and kingdom quests offer objectives that reward resources or bonuses.
- Modifiers from completed tech, buildings, projects, treaties and other effects are aggregated by `get_total_modifiers` in `services/progression_service.py` to calculate a kingdom’s bonuses.

## 6. Diplomacy and War
- Treaties between kingdoms or alliances are stored in `kingdom_treaties` and `alliance_treaties`. Active treaties provide modifiers and can expire over time.
- Wars are tracked in `wars` for strategic declarations and in `wars_tactical` for real-time battles. The tactical record includes phases (`alert` → `planning` → `live` → `resolved`), battle ticks and configuration flags.
- Participants, pre-plans and combat logs all reference the war ID, tying diplomacy and military actions together.

## 7. Strategic Tick
- Periodic maintenance tasks are performed by `process_tick` in `services/strategic_tick_service.py`. It updates project progress, quest status, treaty expiration, activates scheduled wars and concludes finished wars.
- These automated updates keep game state consistent even when players are offline.

## 8. History and Achievements
- Significant actions are logged in `kingdom_history_log` for players to review. When an achievement is unlocked it is also logged and the achievement's points are added to the kingdom's `prestige_score` for leaderboard ranking.

## 9. Overall Flow
1. **Onboarding** creates the baseline kingdom state.
2. **Progression** loops drive players to gather resources, train troops, complete projects and participate in diplomacy.
3. **Strategic Tick** processes ongoing timers and keeps wars and treaties up to date.
4. **Modifiers** from regions, buildings, projects and treaties aggregate to shape each kingdom’s capabilities.
5. **Wars and quests** feed back into progression by providing resources and prestige, restarting the loops.

This schema summarizes how the game's major systems work together so new features can be integrated coherently.
