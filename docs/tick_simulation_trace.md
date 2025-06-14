# 🔁 Strategic Tick Simulation Trace

This guide provides a step-by-step log-style walkthrough of a full game tick using `process_tick()`.

## Example Tick Log (Kingdom ID 42)

**⏱ Tick Start: 2025-06-14 01:00 UTC**

1. ✅ Quests Updated:
   - `quest_kingdom_tracking`: Progressed 12 → 25%
   - `quest_alliance_tracking`: Completed 100%, marked "completed"

2. 🛠 Projects Advanced:
   - Player Project: `foundries_of_ember` → 300s remaining
   - Alliance Project: `great_wall` completed!

3. ⚔️ Wars Advanced:
   - War ID 17 (tactical): Tick 5 → 6, combat log written
   - Castle HP: 8700 → 8100 (attacker hit)

4. 📜 Treaties Expired:
   - Treaty #12 expired (5-day NAP)

5. 💰 Village Production:
   - `village_id=8` produced +180 wood
   - `village_id=9` produced +120 iron_ore

**⏱ Tick Complete: Duration 78ms**